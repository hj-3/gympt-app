package com.gympt.backend.controller;

import com.gympt.backend.service.AgentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
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
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestBody Map<String, Object> request) {

        log.info("Workout recommendation request from user: {}", userDetails.getUsername());

        Map<String, Object> response = agentService.getWorkoutRecommendation(request);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/posture-feedback")
    public ResponseEntity<Map<String, Object>> getPostureFeedback(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestBody Map<String, Object> request) {

        log.info("Posture feedback request from user: {}", userDetails.getUsername());

        Map<String, Object> response = agentService.getPostureFeedback(request);
        return ResponseEntity.ok(response);
    }
}
