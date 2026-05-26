package com.gympt.backend.service;

import com.gympt.backend.dto.WorkoutRecommendationDto;
import com.gympt.backend.entity.BodyProfile;
import com.gympt.backend.entity.User;
import com.gympt.backend.entity.WorkoutRecommendation;
import com.gympt.backend.repository.BodyProfileRepository;
import com.gympt.backend.repository.UserRepository;
import com.gympt.backend.repository.WorkoutRecommendationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentService {

    private final RestTemplate restTemplate;
    private final UserRepository userRepository;
    private final BodyProfileRepository bodyProfileRepository;
    private final WorkoutRecommendationRepository workoutRecommendationRepository;

    @Value("${app.services.agent.base-url}")
    private String agentServiceUrl;

    public Map<String, Object> getWorkoutRecommendation(UUID userId, Map<String, Object> request) {
        String url = agentServiceUrl + "/agent/workout/recommend";
        log.info("Calling agent service: {} for user: {}", url, userId);

        // Fetch user
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // Fetch latest body profile
        BodyProfile bodyProfile = null;
        List<BodyProfile> profiles = bodyProfileRepository.findByUser_IdOrderByMeasurementDateDesc(
                userId, PageRequest.of(0, 1)
        );
        if (!profiles.isEmpty()) {
            bodyProfile = profiles.get(0);
            log.info("Found body profile for user {}: height={}, weight={}", userId, bodyProfile.getHeight(), bodyProfile.getWeight());
        }

        // Add body profile to request if available
        if (bodyProfile != null) {
            request.put("height", bodyProfile.getHeight());
            request.put("weight", bodyProfile.getWeight());
            request.put("body_fat", bodyProfile.getBodyFat());
            request.put("muscle_mass", bodyProfile.getMuscleMass());
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);

            // Save recommendation to database
            if (response != null && response.containsKey("recommendation")) {
                WorkoutRecommendation recommendation = WorkoutRecommendation.builder()
                        .user(user)
                        .recommendation((String) response.get("recommendation"))
                        .interactionId((String) response.get("interaction_id"))
                        .goal((String) request.get("goal"))
                        .fitnessLevel((String) request.get("fitness_level"))
                        .daysPerWeek((Integer) request.get("days_per_week"))
                        .equipmentAvailable(request.get("equipment_available") != null ?
                                String.join(",", (List<String>) request.get("equipment_available")) : null)
                        .injuriesOrLimitations((String) request.get("injuries_or_limitations"))
                        .modelUsed((String) response.get("model_used"))
                        .sessionId((String) response.get("session_id"))
                        .height(bodyProfile != null ? bodyProfile.getHeight() : null)
                        .weight(bodyProfile != null ? bodyProfile.getWeight() : null)
                        .bodyFat(bodyProfile != null ? bodyProfile.getBodyFat() : null)
                        .muscleMass(bodyProfile != null ? bodyProfile.getMuscleMass() : null)
                        .build();

                WorkoutRecommendation saved = workoutRecommendationRepository.save(recommendation);
                log.info("Saved workout recommendation with ID: {}", saved.getId());

                // Add saved ID to response
                response.put("id", saved.getId().toString());
            }

            return response;
        } catch (Exception e) {
            log.error("Failed to get workout recommendation from agent service: {}", e.getMessage());
            throw new RuntimeException("AI 코치 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.", e);
        }
    }

    public List<WorkoutRecommendationDto> getWorkoutRecommendationHistory(UUID userId, int limit) {
        List<WorkoutRecommendation> recommendations;
        if (limit > 0) {
            recommendations = workoutRecommendationRepository.findByUser_IdOrderByCreatedAtDesc(
                    userId, PageRequest.of(0, limit)
            );
        } else {
            recommendations = workoutRecommendationRepository.findByUser_IdOrderByCreatedAtDesc(userId);
        }

        return recommendations.stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    public WorkoutRecommendationDto getWorkoutRecommendationById(UUID id) {
        WorkoutRecommendation recommendation = workoutRecommendationRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Recommendation not found"));
        return toDto(recommendation);
    }

    private WorkoutRecommendationDto toDto(WorkoutRecommendation recommendation) {
        return WorkoutRecommendationDto.builder()
                .id(recommendation.getId())
                .recommendation(recommendation.getRecommendation())
                .interactionId(recommendation.getInteractionId())
                .goal(recommendation.getGoal())
                .fitnessLevel(recommendation.getFitnessLevel())
                .daysPerWeek(recommendation.getDaysPerWeek())
                .equipmentAvailable(recommendation.getEquipmentAvailable())
                .injuriesOrLimitations(recommendation.getInjuriesOrLimitations())
                .modelUsed(recommendation.getModelUsed())
                .sessionId(recommendation.getSessionId())
                .height(recommendation.getHeight())
                .weight(recommendation.getWeight())
                .bodyFat(recommendation.getBodyFat())
                .muscleMass(recommendation.getMuscleMass())
                .createdAt(recommendation.getCreatedAt())
                .updatedAt(recommendation.getUpdatedAt())
                .build();
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
