package com.aquaculture.backend_orchestrator;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@RestController
@RequestMapping("/api")
public class DebrisController {

    @PostMapping({"/analyze", "/analyze-upload"})
    public ResponseEntity<Map<String, Object>> analyzeUpload(@RequestParam("file") MultipartFile file) {
        File inputFile = null;
        File outputFile = null;
        ExecutorService streamReaders = Executors.newFixedThreadPool(2);
        try {
            String uniqueId = UUID.randomUUID().toString();
            File outputDir = new File(System.getProperty("java.io.tmpdir"), "aquatic-analysis");
            Files.createDirectories(outputDir.toPath());
            inputFile = new File(outputDir, "input-" + uniqueId + ".jpg");
            outputFile = new File(outputDir, "output-" + uniqueId + ".jpg");
            file.transferTo(inputFile);

            File pythonScript = resolveInferenceScript();
            String pythonExecutable = System.getenv().getOrDefault("PYTHON_EXECUTABLE", "python3");
            ProcessBuilder pb = new ProcessBuilder(
                    pythonExecutable,
                    pythonScript.getAbsolutePath(),
                    inputFile.getAbsolutePath(),
                    outputFile.getAbsolutePath()
            );
            Process process = pb.start();

            var stdout = streamReaders.submit(() -> readStream(process.getInputStream()));
            var stderr = streamReaders.submit(() -> readStream(process.getErrorStream()));
            long timeoutSeconds = Long.parseLong(
                    System.getenv().getOrDefault("INFERENCE_TIMEOUT_SECONDS", "180")
            );
            if (!process.waitFor(timeoutSeconds, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                Map<String, Object> timeout = new HashMap<>();
                timeout.put("error", "Image analysis timed out after " + timeoutSeconds + " seconds.");
                return ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).body(timeout);
            }
            int exitCode = process.exitValue();
            String standardOutput = stdout.get(10, TimeUnit.SECONDS);
            String standardError = stderr.get(10, TimeUnit.SECONDS);
            System.out.println("Python exit code: " + exitCode);
            if (!standardError.isBlank()) {
                System.err.println("Python stderr: " + standardError);
            }

            if (exitCode != 0) {
                Map<String, Object> failure = new HashMap<>();
                failure.put("error", "Image analysis process failed.");
                failure.put("details", truncate(standardError.isBlank() ? standardOutput : standardError));
                return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(failure);
            }

            String jsonString = extractJson(standardOutput);
            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> result = mapper.readValue(
                    jsonString, new TypeReference<Map<String, Object>>() {}
            );
            result.put("sessionId", uniqueId);
            if (result.containsKey("error")) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(result);
            }
            if (outputFile.exists()) {
                byte[] imageBytes = Files.readAllBytes(outputFile.toPath());
                result.put("annotatedImageUrl", "data:image/jpeg;base64,"
                        + Base64.getEncoder().encodeToString(imageBytes));
            }
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            e.printStackTrace();
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage() != null ? e.getMessage() : "Unknown analysis failure");
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(error);
        } finally {
            streamReaders.shutdownNow();
            deleteIfExists(inputFile);
            deleteIfExists(outputFile);
        }
    }

    private File resolveInferenceScript() throws IOException {
        String configured = System.getenv("INFERENCE_SCRIPT");
        File[] candidates = {
                configured == null || configured.isBlank() ? null : new File(configured),
                new File(System.getProperty("user.dir"), "py_scripts/predict.py"),
                new File(System.getProperty("user.dir"), "../py_scripts/predict.py"),
                new File("/app/py_scripts/predict.py")
        };
        for (File candidate : candidates) {
            if (candidate != null && candidate.isFile() && candidate.canRead()) {
                return candidate.getCanonicalFile();
            }
        }
        throw new IOException("Inference script not found. Set INFERENCE_SCRIPT or ensure py_scripts/predict.py is deployed.");
    }

    private String readStream(InputStream stream) throws IOException {
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
            String line;
            while ((line = reader.readLine()) != null && output.length() < 20000) {
                output.append(line).append('\n');
            }
        }
        return output.toString();
    }

    private String extractJson(String output) {
        int start = output.lastIndexOf("---JSON_START---");
        int end = output.lastIndexOf("---JSON_END---");
        if (start < 0 || end <= start) {
            throw new IllegalStateException("Could not parse inference output: " + truncate(output));
        }
        return output.substring(start + "---JSON_START---".length(), end).trim();
    }

    private String truncate(String value) {
        return value.length() > 4000 ? value.substring(0, 4000) : value;
    }

    private void deleteIfExists(File file) {
        if (file != null && file.exists() && !file.delete()) {
            file.deleteOnExit();
        }
    }
}