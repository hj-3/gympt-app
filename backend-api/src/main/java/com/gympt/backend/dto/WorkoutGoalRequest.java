package com.gympt.backend.dto;

import com.gympt.backend.domain.WorkoutGoal;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WorkoutGoalRequest {

    @NotNull(message = "Goal type is required")
    private WorkoutGoal.GoalType goalType;

    private BigDecimal targetValue;

    private LocalDate targetDate;

    @Size(max = 1000, message = "Description must be less than 1000 characters")
    private String description;
}
