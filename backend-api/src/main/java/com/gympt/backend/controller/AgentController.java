package com.gympt.backend.controller;

import com.gympt.backend.service.AgentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

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

        String userId = authentication.getName(); // DB user UUID
        log.info("Workout recommendation request from user: {}", userId);

        Map<String, Object> response = agentService.getWorkoutRecommendation(request);
        return ResponseEntity.ok(response);
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
