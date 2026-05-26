package com.gympt.backend.controller;

import com.gympt.backend.dto.WorkoutRecommendationDto;
import com.gympt.backend.service.AgentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/agent")
@RequiredArgsConstructor
public class AgentController {

    private final AgentService agentService;

    @PostMapping("/workout-recommendation")
    public ResponseEntity<Map<String, Object>> getWorkoutRecommendation(
            Authentication authentication,
            @RequestBody Map<String, Object> request) {

        UUID userId = UUID.fromString(authentication.getName()); // DB user UUID
        log.info("Workout recommendation request from user: {}", userId);

        Map<String, Object> response = agentService.getWorkoutRecommendation(userId, request);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/workout-recommendations")
    public ResponseEntity<List<WorkoutRecommendationDto>> getWorkoutRecommendations(
            Authentication authentication,
            @RequestParam(required = false, defaultValue = "10") int limit) {

        UUID userId = UUID.fromString(authentication.getName()); // DB user UUID
        log.info("Get workout recommendations for user: {}, limit: {}", userId, limit);

        List<WorkoutRecommendationDto> recommendations = agentService.getWorkoutRecommendationHistory(userId, limit);
        return ResponseEntity.ok(recommendations);
    }

    @GetMapping("/workout-recommendations/{id}")
    public ResponseEntity<WorkoutRecommendationDto> getWorkoutRecommendationById(
            Authentication authentication,
            @PathVariable UUID id) {

        UUID userId = UUID.fromString(authentication.getName()); // DB user UUID
        log.info("Get workout recommendation {} for user: {}", id, userId);

        WorkoutRecommendationDto recommendation = agentService.getWorkoutRecommendationById(id);
        return ResponseEntity.ok(recommendation);
    }

    @PostMapping("/posture-feedback")
    public ResponseEntity<Map<String, Object>> getPostureFeedback(
            Authentication authentication,
            @RequestBody Map<String, Object> request) {

        String userId = authentication.getName(); // DB user UUID
        log.info("Posture feedback request from user: {}", userId);

        Map<String, Object> response = agentService.getPostureFeedback(request);
        return ResponseEntity.ok(response);
    }
}
