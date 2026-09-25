package com.aquaculture.backend_orchestrator;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class DebrisController {

    @PostMapping({"/analyze", "/analyze-upload"})
    public ResponseEntity<Map<String, String>> analyzeUpload(@RequestParam("file") MultipartFile file) {
        File inputFile = null;
        try {
            String projectDir = System.getProperty("user.dir");

            // 1. Output directory
            File outputDir = new File(projectDir, "src/main/resources/static/outputs");
            if (!outputDir.exists()) outputDir.mkdirs();

            // 2. Save temporary uploaded file
            String uniqueId = UUID.randomUUID().toString();
            String fileName = uniqueId + ".jpg";
            inputFile = new File(System.getProperty("java.io.tmpdir"), "input_" + fileName);
            file.transferTo(inputFile);

            // 3. Output target for Python
            File outputFile = new File(outputDir, fileName);

            // 4. Execute Python script
            String pythonScriptPath = new File(projectDir, "../py_scripts/predict.py").getCanonicalPath();

            ProcessBuilder pb = new ProcessBuilder(
                    "python3",
                    pythonScriptPath,
                    inputFile.getAbsolutePath(),
                    outputFile.getAbsolutePath()
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();

            // 5. Read output
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder consoleOutput = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                consoleOutput.append(line).append("\n");
                System.out.println("Python: " + line);
            }
            int exitCode = process.waitFor();

            // 6. Parse response & attach Base64 Image
            String outputStr = consoleOutput.toString();
            if (outputStr.contains("---JSON_START---") && outputStr.contains("---JSON_END---")) {
                String jsonString = outputStr.substring(
                        outputStr.indexOf("---JSON_START---") + 16,
                        outputStr.indexOf("---JSON_END---")
                );

                ObjectMapper mapper = new ObjectMapper();
                Map<String, String> result = mapper.readValue(jsonString, new TypeReference<Map<String, String>>() {});

                result.put("sessionId", uniqueId);

                // Check if Python reported an explicit error in the JSON payload
                if (result.containsKey("error")) {
                    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(result);
                }

                // Convert the saved image directly into a Base64 data URI
                if (outputFile.exists()) {
                    byte[] imageBytes = Files.readAllBytes(outputFile.toPath());
                    String base64Image = Base64.getEncoder().encodeToString(imageBytes);
                    result.put("annotatedImageUrl", "data:image/jpeg;base64," + base64Image);
                }

                return ResponseEntity.ok(result);
            } else {
                String details = outputStr.isBlank() ? ("Process exited with code " + exitCode) : outputStr.trim();
                throw new RuntimeException("Could not parse JSON from Python script. Python output: " + details);
            }

        } catch (Exception e) {
            e.printStackTrace();
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage() != null ? e.getMessage() : "Unknown analysis failure");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        } finally {
            if (inputFile != null && inputFile.exists()) {
                inputFile.delete();
            }
        }
    }
}