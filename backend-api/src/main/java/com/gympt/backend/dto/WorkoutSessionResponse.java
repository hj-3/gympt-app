package com.gympt.backend.dto;

import com.gympt.backend.domain.WorkoutSession;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WorkoutSessionResponse {

    private UUID id;
    private UUID userId;
    private UUID workoutPlanId;
    private Instant startTime;
    private Instant endTime;
    private WorkoutSession.SessionStatus status;
    private Integer totalDuration;
    private BigDecimal caloriesBurned;
    private String notes;
    private Instant createdAt;
    private Instant updatedAt;

    public static WorkoutSessionResponse from(WorkoutSession session) {
        return WorkoutSessionResponse.builder()
            .id(session.getId())
            .userId(session.getUser().getId())
            .workoutPlanId(session.getWorkoutPlan() != null ? session.getWorkoutPlan().getId() : null)
            .startTime(session.getStartTime())
            .endTime(session.getEndTime())
            .status(session.getStatus())
            .totalDuration(session.getTotalDuration())
            .caloriesBurned(session.getCaloriesBurned())
            .notes(session.getNotes())
            .createdAt(session.getCreatedAt())
            .updatedAt(session.getUpdatedAt())
            .build();
    }
}
