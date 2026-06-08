package com.gympt.backend.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EndWorkoutSessionRequest {

    @Min(value = 1, message = "Total duration must be at least 1 second")
    private Integer totalDuration;

    @DecimalMin(value = "0.0", message = "Calories burned must be at least 0")
    private BigDecimal caloriesBurned;

    @Size(max = 2000, message = "Notes must be less than 2000 characters")
    private String notes;

    private String exerciseType;

    private String exerciseName;

    private Integer totalReps;

    @DecimalMin(value = "0.0")
    private BigDecimal avgPostureScore;

    private UUID recommendationId;
}
