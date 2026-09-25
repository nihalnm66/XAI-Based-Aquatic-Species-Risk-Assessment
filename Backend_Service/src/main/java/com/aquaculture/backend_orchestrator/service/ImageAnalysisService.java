package com.aquaculture.backend_orchestrator.service;

import com.aquaculture.backend_orchestrator.entity.DetectionResult;
import com.aquaculture.backend_orchestrator.repository.DetectionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ImageAnalysisService {

    private final DetectionRepository detectionRepository;

    public DetectionResult processAnalysis(MultipartFile file) {
        try {
            // 1. Save the file to the system's absolute temp directory
            String fileName = UUID.randomUUID().toString() + ".jpg";
            String tempDir = System.getProperty("java.io.tmpdir");
            File destFile = new File(tempDir, fileName);

            file.transferTo(destFile);
            String absolutePath = destFile.getAbsolutePath();

            // 2. Execute the python3 script using the absolute file path
            ProcessBuilder processBuilder = new ProcessBuilder("python3", "py_scripts/predict.py", absolutePath);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line);
            }
            process.waitFor();

            // 3. Save the result to PostgreSQL
            DetectionResult result = new DetectionResult();
            result.setSessionId(UUID.randomUUID().toString());
            result.setAnalysisSummary(output.toString());
            result.setOverallRiskScore(output.toString().contains("HIGH") ? "HIGH" : "LOW");

            return detectionRepository.save(result);

        } catch (Exception e) {
            DetectionResult errorResult = new DetectionResult();
            errorResult.setSessionId(UUID.randomUUID().toString());
            errorResult.setAnalysisSummary("---JSON_START---{\"error\": \"" + e.getMessage().replace("\"", "'") + "\"}---JSON_END---");
            errorResult.setOverallRiskScore("LOW");
            return errorResult;
        }
    }
}