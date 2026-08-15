package com.aquaculture.backend_orchestrator.controller;

import com.aquaculture.backend_orchestrator.entity.DetectionResult;
import com.aquaculture.backend_orchestrator.repository.DetectionRepository;
import com.aquaculture.backend_orchestrator.service.ImageAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class AnalysisController {

    private final ImageAnalysisService analysisService;
    private final DetectionRepository detectionRepository; // Inject repository directly for quick querying

    @PostMapping("/analyze")
    public ResponseEntity<DetectionResult> analyzeImage(@RequestParam("path") String imagePath) {
        DetectionResult result = analysisService.processAnalysis(imagePath);
        return ResponseEntity.ok(result);
    }

    // NEW: Endpoint to fetch all analysis history from PostgreSQL
    @GetMapping("/history")
    public ResponseEntity<List<DetectionResult>> getAllResults() {
        List<DetectionResult> results = detectionRepository.findAll();
        return ResponseEntity.ok(results);
    }
}