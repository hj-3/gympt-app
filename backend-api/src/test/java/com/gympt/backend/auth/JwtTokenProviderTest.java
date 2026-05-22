package com.gympt.backend.auth;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.List;
import java.util.Base64;

import static org.assertj.core.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;

    @BeforeEach
    void setUp() {
        // Create a valid base64-encoded 256-bit secret
        String secret = Base64.getEncoder().encodeToString(
            "test-secret-key-for-jwt-token-signing-must-be-at-least-256-bits".getBytes()
        );
        jwtTokenProvider = new JwtTokenProvider(secret, 3600, 86400);
    }

    @Test
    @DisplayName("Should generate valid access token")
    void shouldGenerateValidAccessToken() {
        // Arrange
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            "user-id-123",
            null,
            List.of(new SimpleGrantedAuthority("ROLE_USER"))
        );

        // Act
        String token = jwtTokenProvider.generateAccessToken(authentication);

        // Assert
        assertThat(token).isNotNull();
        assertThat(token).contains(".");
        assertThat(jwtTokenProvider.validateToken(token)).isTrue();
    }

    @Test
    @DisplayName("Should extract user ID from token")
    void shouldExtractUserIdFromToken() {
        // Arrange
        String userId = "user-id-456";
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            userId,
            null,
            List.of(new SimpleGrantedAuthority("ROLE_USER"))
        );
        String token = jwtTokenProvider.generateAccessToken(authentication);

        // Act
        String extractedUserId = jwtTokenProvider.getUserIdFromToken(token);

        // Assert
        assertThat(extractedUserId).isEqualTo(userId);
    }

    @Test
    @DisplayName("Should invalidate malformed token")
    void shouldInvalidateMalformedToken() {
        // Arrange
        String malformedToken = "invalid.token.here";

        // Act & Assert
        assertThat(jwtTokenProvider.validateToken(malformedToken)).isFalse();
    }

    @Test
    @DisplayName("Should generate refresh token")
    void shouldGenerateRefreshToken() {
        // Arrange
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            "user-id-789",
            null,
            List.of(new SimpleGrantedAuthority("ROLE_USER"))
        );

        // Act
        String refreshToken = jwtTokenProvider.generateRefreshToken(authentication);

        // Assert
        assertThat(refreshToken).isNotNull();
        assertThat(jwtTokenProvider.validateToken(refreshToken)).isTrue();
    }
}
