package com.gympt.backend.dto;

import com.gympt.backend.domain.WorkoutGoal;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WorkoutGoalResponse {

    private UUID id;
    private UUID userId;
    private WorkoutGoal.GoalType goalType;
    private BigDecimal targetValue;
    private LocalDate targetDate;
    private WorkoutGoal.GoalStatus status;
    private String description;
    private Instant createdAt;
    private Instant updatedAt;

    public static WorkoutGoalResponse from(WorkoutGoal goal) {
        return WorkoutGoalResponse.builder()
            .id(goal.getId())
            .userId(goal.getUser().getId())
            .goalType(goal.getGoalType())
            .targetValue(goal.getTargetValue())
            .targetDate(goal.getTargetDate())
            .status(goal.getStatus())
            .description(goal.getDescription())
            .createdAt(goal.getCreatedAt())
            .updatedAt(goal.getUpdatedAt())
            .build();
    }
}
