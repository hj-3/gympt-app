package com.gympt.backend.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentService {

    private final RestTemplate restTemplate;

    @Value("${app.services.agent.base-url}")
    private String agentServiceUrl;

    public Map<String, Object> getWorkoutRecommendation(Map<String, Object> request) {
        String url = agentServiceUrl + "/agent/workout/recommend";
        log.info("Calling agent service: {}", url);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);
            return response;
        } catch (Exception e) {
            log.error("Failed to get workout recommendation from agent service", e);
            throw new RuntimeException("Agent service unavailable", e);
        }
    }

    public Map<String, Object> getPostureFeedback(Map<String, Object> request) {
        String url = agentServiceUrl + "/agent/posture/feedback";
        log.info("Calling agent service: {}", url);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);
            return response;
        } catch (Exception e) {
            log.error("Failed to get posture feedback from agent service", e);
            throw new RuntimeException("Agent service unavailable", e);
        }
    }
}
