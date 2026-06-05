package com.gympt.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutRecommendationDto {
    private UUID id;
    private String recommendation;
    private String interactionId;
    private String goal;
    private String fitnessLevel;
    private Integer daysPerWeek;
    private String equipmentAvailable;
    private String injuriesOrLimitations;
    private String modelUsed;
    private String sessionId;
    private String targetExercises;
    private Double height;
    private Double weight;
    private Double bodyFat;
    private Double muscleMass;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
