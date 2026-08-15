package com.aquaculture.backend_orchestrator.service;

import com.aquaculture.backend_orchestrator.entity.DetectionResult;
import com.aquaculture.backend_orchestrator.repository.DetectionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ImageAnalysisService {

    private final DetectionRepository detectionRepository;

    public DetectionResult processAnalysis(String originalImagePath) {
        DetectionResult result = new DetectionResult();
        result.setSessionId(UUID.randomUUID().toString());
        result.setOriginalImagePath(originalImagePath);

        try {
            // Execute the Python script and pass the image path argument
            ProcessBuilder processBuilder = new ProcessBuilder(
                    "python3",
                    "../py_scripts/predict.py",
                    "--image", originalImagePath
            );

            Process process = processBuilder.start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;

            while ((line = reader.readLine()) != null) {
                output.append(line);
            }

            process.waitFor();

            String outputStr = output.toString();
            result.setHeatmapPath("outputs/heatmap_" + originalImagePath);
            result.setAnalysisSummary(outputStr.isEmpty() ? "Inference executed successfully." : outputStr);
            result.setOverallRiskScore(outputStr.contains("HIGH") ? "HIGH" : "LOW");

        } catch (Exception e) {
            result.setAnalysisSummary("Execution error: " + e.getMessage());
            result.setOverallRiskScore("UNKNOWN");
        }

        return detectionRepository.save(result);
    }
}