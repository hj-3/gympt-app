package com.gympt.backend.dto;

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
public class WorkoutSessionRequest {

    private UUID workoutPlanId;

    @Size(max = 2000, message = "Notes must be less than 2000 characters")
    private String notes;
}
