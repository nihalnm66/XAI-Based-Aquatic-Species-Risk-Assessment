package com.aquaculture.backend_orchestrator.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Entity
@Table(name = "detection_results")
@Data
public class DetectionResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String sessionId;
    private String originalImagePath;
    private String heatmapPath;

    @Column(columnDefinition = "TEXT")
    private String analysisSummary;

    private String overallRiskScore;

    @Transient
    private String xaiHeatmapUrl;

    @Transient
    private List<Map<String, Object>> speciesDetections;

    @Transient
    private List<Map<String, Object>> debrisDetections;

    private LocalDateTime createdAt = LocalDateTime.now();
}