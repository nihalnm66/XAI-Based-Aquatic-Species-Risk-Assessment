package com.aquaculture.backend_orchestrator;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class DebrisController {

    @PostMapping("/analyze-upload")
    public ResponseEntity<Map<String, String>> analyzeUpload(@RequestParam("file") MultipartFile file) {
        try {
            String projectDir = System.getProperty("user.dir"); // This is your Backend_Service folder

            // 1. Create a folder to store the output images so the frontend can display them
            File outputDir = new File(projectDir, "src/main/resources/static/outputs");
            if (!outputDir.exists()) outputDir.mkdirs();

            // 2. Save the uploaded file temporarily
            String uniqueId = UUID.randomUUID().toString();
            String fileName = uniqueId + ".jpg";
            File inputFile = new File(System.getProperty("java.io.tmpdir"), "input_" + fileName);
            file.transferTo(inputFile);

            // 3. Define where Python should save the annotated image
            File outputFile = new File(outputDir, fileName);

            // 4. Setup Python Script Execution
            String pythonScriptPath = new File(projectDir, "../py_scripts/predict.py").getCanonicalPath();

            ProcessBuilder pb = new ProcessBuilder(
                    "python3", // Use python3 for Mac
                    pythonScriptPath,
                    inputFile.getAbsolutePath(),
                    outputFile.getAbsolutePath()
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();

            // 5. Read Python Output
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder consoleOutput = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                consoleOutput.append(line);
                System.out.println("Python: " + line); // Print YOLO logs to IntelliJ console
            }
            process.waitFor();

            // 6. Extract the JSON from Python output
            String outputStr = consoleOutput.toString();
            if(outputStr.contains("---JSON_START---") && outputStr.contains("---JSON_END---")) {
                String jsonString = outputStr.substring(
                        outputStr.indexOf("---JSON_START---") + 16,
                        outputStr.indexOf("---JSON_END---")
                );

                // Parse the JSON into a Map
                ObjectMapper mapper = new ObjectMapper();
                Map<String, String> result = mapper.readValue(jsonString, new TypeReference<Map<String, String>>(){});

                // Add the frontend variables
                result.put("sessionId", uniqueId);
                result.put("annotatedImageUrl", "/outputs/" + fileName); // Path for the frontend to load image

                return ResponseEntity.ok(result);
            } else {
                throw new RuntimeException("Could not parse JSON from Python script.");
            }

        } catch (Exception e) {
            e.printStackTrace();
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(500).body(error);
        }
    }
}