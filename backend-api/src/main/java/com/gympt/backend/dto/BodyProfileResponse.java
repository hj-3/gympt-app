package com.gympt.backend.dto;

import com.gympt.backend.domain.BodyProfile;
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
public class BodyProfileResponse {

    private UUID id;
    private UUID userId;
    private BigDecimal height;
    private BigDecimal weight;
    private BigDecimal bodyFat;
    private BigDecimal muscleMass;
    private BodyProfile.PostureType postureType;
    private LocalDate measurementDate;
    private Instant createdAt;
    private Instant updatedAt;

    public static BodyProfileResponse from(BodyProfile profile) {
        return BodyProfileResponse.builder()
            .id(profile.getId())
            .userId(profile.getUser().getId())
            .height(profile.getHeight())
            .weight(profile.getWeight())
            .bodyFat(profile.getBodyFat())
            .muscleMass(profile.getMuscleMass())
            .postureType(profile.getPostureType())
            .measurementDate(profile.getMeasurementDate())
            .createdAt(profile.getCreatedAt())
            .updatedAt(profile.getUpdatedAt())
            .build();
    }
}
