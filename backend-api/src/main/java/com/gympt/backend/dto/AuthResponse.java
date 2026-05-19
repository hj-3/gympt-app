package com.gympt.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthResponse {

    private UUID userId;
    private String accessToken;
    private String refreshToken;
    private String tokenType;
    private Long expiresIn;

    public static AuthResponse of(UUID userId, String accessToken, String refreshToken, Long expiresIn) {
        return AuthResponse.builder()
            .userId(userId)
            .accessToken(accessToken)
            .refreshToken(refreshToken)
            .tokenType("Bearer")
            .expiresIn(expiresIn)
            .build();
    }
}
