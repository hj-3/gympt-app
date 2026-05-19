package com.gympt.backend.dto;

import com.gympt.backend.domain.BodyProfile;
import jakarta.validation.constraints.*;
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
public class BodyProfileRequest {

    @NotNull(message = "Height is required")
    @DecimalMin(value = "50.0", message = "Height must be at least 50 cm")
    @DecimalMax(value = "300.0", message = "Height must be less than 300 cm")
    private BigDecimal height;

    @NotNull(message = "Weight is required")
    @DecimalMin(value = "20.0", message = "Weight must be at least 20 kg")
    @DecimalMax(value = "500.0", message = "Weight must be less than 500 kg")
    private BigDecimal weight;

    @DecimalMin(value = "0.0", message = "Body fat must be at least 0%")
    @DecimalMax(value = "100.0", message = "Body fat must be less than 100%")
    private BigDecimal bodyFat;

    @DecimalMin(value = "0.0", message = "Muscle mass must be at least 0 kg")
    private BigDecimal muscleMass;

    private BodyProfile.PostureType postureType;

    @NotNull(message = "Measurement date is required")
    private LocalDate measurementDate;
}
