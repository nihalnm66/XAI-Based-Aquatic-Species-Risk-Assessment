package com.aquaculture.backend_orchestrator.repository;

import com.aquaculture.backend_orchestrator.entity.DetectionResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DetectionRepository extends JpaRepository<DetectionResult, Long> {
}