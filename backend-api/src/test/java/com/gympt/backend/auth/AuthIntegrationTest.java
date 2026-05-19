package com.gympt.backend.auth;

import com.gympt.backend.BaseIntegrationTest;
import com.gympt.backend.domain.RefreshToken;
import com.gympt.backend.dto.AuthRequest;
import com.gympt.backend.dto.AuthResponse;
import com.gympt.backend.dto.RefreshTokenRequest;
import com.gympt.backend.dto.RegisterRequest;
import com.gympt.backend.user.User;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;

import java.time.Instant;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for Authentication flow.
 * Tests register, login, token refresh, and logout operations with real database.
 */
@DisplayName("Auth Integration Tests")
class AuthIntegrationTest extends BaseIntegrationTest {

    @Nested
    @DisplayName("Register Tests")
    class RegisterTests {

        @Test
        @DisplayName("Should register new user successfully")
        void shouldRegisterSuccessfully() throws Exception {
            // Arrange
            RegisterRequest request = RegisterRequest.builder()
                .email("newuser@example.com")
                .password("Password123!")
                .name("New User")
                .age(28)
                .gender(User.Gender.MALE)
                .fitnessLevel(User.FitnessLevel.BEGINNER)
                .build();

            // Act & Assert
            MvcResult result = mockMvc.perform(post("/api/v1/auth/register")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").exists())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andExpect(jsonPath("$.expiresIn").exists())
                .andReturn();

            // Verify user was created in database
            User savedUser = userRepository.findByEmail(request.getEmail()).orElse(null);
            assertThat(savedUser).isNotNull();
            assertThat(savedUser.getName()).isEqualTo(request.getName());
            assertThat(savedUser.getStatus()).isEqualTo(User.UserStatus.ACTIVE);
        }

        @Test
        @DisplayName("Should reject registration with duplicate email")
        void shouldRejectDuplicateEmail() throws Exception {
            // Arrange
            RegisterRequest request = RegisterRequest.builder()
                .email(testUser.getEmail()) // Using existing test user email
                .password("Password123!")
                .name("Another User")
                .age(30)
                .gender(User.Gender.FEMALE)
                .fitnessLevel(User.FitnessLevel.INTERMEDIATE)
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/register")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("Email already exists"));
        }

        @Test
        @DisplayName("Should reject registration with invalid data")
        void shouldRejectInvalidData() throws Exception {
            // Arrange
            RegisterRequest request = RegisterRequest.builder()
                .email("invalid-email") // Invalid email format
                .password("short")
                .name("")
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/register")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
        }
    }

    @Nested
    @DisplayName("Login Tests")
    class LoginTests {

        @Test
        @DisplayName("Should login successfully with valid credentials")
        void shouldLoginSuccessfully() throws Exception {
            // Arrange
            AuthRequest request = AuthRequest.builder()
                .email(testUser.getEmail())
                .password("Password123!")
                .build();

            // Act & Assert
            MvcResult result = mockMvc.perform(post("/api/v1/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value(testUser.getId().toString()))
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andReturn();

            // Verify last login was updated
            User updatedUser = userRepository.findById(testUser.getId()).orElse(null);
            assertThat(updatedUser).isNotNull();
            assertThat(updatedUser.getLastLoginAt()).isNotNull();
            assertThat(updatedUser.getLastLoginAt()).isAfter(Instant.now().minusSeconds(10));
        }

        @Test
        @DisplayName("Should reject login with wrong password")
        void shouldRejectWrongPassword() throws Exception {
            // Arrange
            AuthRequest request = AuthRequest.builder()
                .email(testUser.getEmail())
                .password("WrongPassword!")
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Invalid email or password"));
        }

        @Test
        @DisplayName("Should reject login with non-existent email")
        void shouldRejectNonExistentEmail() throws Exception {
            // Arrange
            AuthRequest request = AuthRequest.builder()
                .email("nonexistent@example.com")
                .password("Password123!")
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized());
        }
    }

    @Nested
    @DisplayName("Token Refresh Tests")
    class RefreshTokenTests {

        @Test
        @DisplayName("Should refresh token successfully")
        void shouldRefreshTokenSuccessfully() throws Exception {
            // Arrange
            String refreshToken = testUserRefreshToken;
            RefreshToken savedToken = TestDataFactory.createTestRefreshToken(
                testUser.getId(),
                refreshToken
            );
            refreshTokenRepository.save(savedToken);

            RefreshTokenRequest request = RefreshTokenRequest.builder()
                .refreshToken(refreshToken)
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/refresh")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andExpect(jsonPath("$.userId").value(testUser.getId().toString()));

            // Verify old token was revoked
            RefreshToken oldToken = refreshTokenRepository.findByToken(refreshToken).orElse(null);
            assertThat(oldToken).isNotNull();
            assertThat(oldToken.getRevoked()).isTrue();
        }

        @Test
        @DisplayName("Should reject expired refresh token")
        void shouldRejectExpiredToken() throws Exception {
            // Arrange
            String expiredToken = generateRefreshToken(testUser);
            RefreshToken savedToken = TestDataFactory.createExpiredRefreshToken(
                testUser.getId(),
                expiredToken
            );
            refreshTokenRepository.save(savedToken);

            RefreshTokenRequest request = RefreshTokenRequest.builder()
                .refreshToken(expiredToken)
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/refresh")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Refresh token has expired"));

            // Verify expired token was deleted
            assertThat(refreshTokenRepository.findByToken(expiredToken)).isEmpty();
        }

        @Test
        @DisplayName("Should reject invalid refresh token")
        void shouldRejectInvalidToken() throws Exception {
            // Arrange
            RefreshTokenRequest request = RefreshTokenRequest.builder()
                .refreshToken("invalid-token")
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/refresh")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Invalid refresh token"));
        }

        @Test
        @DisplayName("Should reject revoked refresh token")
        void shouldRejectRevokedToken() throws Exception {
            // Arrange
            String revokedToken = generateRefreshToken(testUser);
            RefreshToken savedToken = TestDataFactory.createTestRefreshToken(
                testUser.getId(),
                revokedToken
            );
            savedToken.setRevoked(true);
            refreshTokenRepository.save(savedToken);

            RefreshTokenRequest request = RefreshTokenRequest.builder()
                .refreshToken(revokedToken)
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/refresh")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Refresh token has been revoked"));
        }
    }

    @Nested
    @DisplayName("Logout Tests")
    class LogoutTests {

        @Test
        @DisplayName("Should logout successfully")
        void shouldLogoutSuccessfully() throws Exception {
            // Arrange
            String refreshToken = generateRefreshToken(testUser);
            RefreshToken savedToken = TestDataFactory.createTestRefreshToken(
                testUser.getId(),
                refreshToken
            );
            refreshTokenRepository.save(savedToken);

            RefreshTokenRequest request = RefreshTokenRequest.builder()
                .refreshToken(refreshToken)
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/logout")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk());

            // Verify token was revoked
            RefreshToken revokedToken = refreshTokenRepository.findByToken(refreshToken).orElse(null);
            assertThat(revokedToken).isNotNull();
            assertThat(revokedToken.getRevoked()).isTrue();
        }

        @Test
        @DisplayName("Should handle logout with already logged out token")
        void shouldHandleAlreadyLoggedOut() throws Exception {
            // Arrange
            RefreshTokenRequest request = RefreshTokenRequest.builder()
                .refreshToken("non-existent-token")
                .build();

            // Act & Assert
            mockMvc.perform(post("/api/v1/auth/logout")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk()); // Should succeed even if token not found
        }
    }

    @Nested
    @DisplayName("Concurrent Operations Tests")
    class ConcurrentTests {

        @Test
        @DisplayName("Should handle concurrent login attempts")
        void shouldHandleConcurrentLogins() throws Exception {
            // Arrange
            AuthRequest request = AuthRequest.builder()
                .email(testUser.getEmail())
                .password("Password123!")
                .build();

            // Act - Simulate two concurrent logins
            MvcResult result1 = mockMvc.perform(post("/api/v1/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andReturn();

            MvcResult result2 = mockMvc.perform(post("/api/v1/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andReturn();

            // Assert - Both should succeed with different tokens
            AuthResponse response1 = objectMapper.readValue(
                result1.getResponse().getContentAsString(),
                AuthResponse.class
            );
            AuthResponse response2 = objectMapper.readValue(
                result2.getResponse().getContentAsString(),
                AuthResponse.class
            );

            assertThat(response1.getAccessToken()).isNotEqualTo(response2.getAccessToken());
            assertThat(response1.getRefreshToken()).isNotEqualTo(response2.getRefreshToken());
        }
    }
}
