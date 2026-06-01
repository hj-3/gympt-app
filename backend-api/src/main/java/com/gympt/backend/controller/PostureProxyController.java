package com.gympt.backend.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/posture")
@RequiredArgsConstructor
@Slf4j
public class PostureProxyController {

    @Value("${gympt.services.posture-analysis.base-url:http://posture-analysis-service-prod:8002}")
    private String postureServiceUrl;

    private final RestTemplate restTemplate;

    @PostMapping("/analyze")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<Map> analyzeFrame(@RequestBody Map<String, Object> request) {
        log.info("Proxying frame analysis to posture-analysis-service");

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

        ResponseEntity<Map> response = restTemplate.exchange(
            postureServiceUrl + "/api/v1/analyze",
            HttpMethod.POST,
            entity,
            Map.class
        );

        return ResponseEntity.status(response.getStatusCode()).body(response.getBody());
    }

    @GetMapping("/exercises")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<Map> getSupportedExercises() {
        ResponseEntity<Map> response = restTemplate.getForEntity(
            postureServiceUrl + "/api/v1/exercises",
            Map.class
        );
        return ResponseEntity.status(response.getStatusCode()).body(response.getBody());
    }
}
