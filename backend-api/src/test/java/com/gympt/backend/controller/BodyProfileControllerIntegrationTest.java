package com.gympt.backend.controller;

import com.gympt.backend.BaseIntegrationTest;
import com.gympt.backend.domain.BodyProfile;
import com.gympt.backend.dto.BodyProfileRequest;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for BodyProfileController.
 * Tests body profile management with authentication and database integration.
 */
@DisplayName("BodyProfileController Integration Tests")
class BodyProfileControllerIntegrationTest extends BaseIntegrationTest {

    @Test
    @DisplayName("Should create body profile successfully")
    void shouldCreateBodyProfileSuccessfully() throws Exception {
        // Arrange
        BodyProfileRequest request = TestDataFactory.createBodyProfileRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/body-profiles")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").exists())
            .andExpect(jsonPath("$.height").value(request.getHeight().doubleValue()))
            .andExpect(jsonPath("$.weight").value(request.getWeight().doubleValue()))
            .andExpect(jsonPath("$.bodyFat").value(request.getBodyFat().doubleValue()))
            .andExpect(jsonPath("$.postureType").value(request.getPostureType().toString()));

        // Verify database
        assertThat(bodyProfileRepository.findAll()).hasSize(1);
    }

    @Test
    @DisplayName("Should get body profile history")
    void shouldGetBodyProfileHistory() throws Exception {
        // Arrange - Create multiple profiles
        BodyProfile profile1 = TestDataFactory.createTestBodyProfile(testUser);
        profile1.setMeasurementDate(LocalDate.now().minusDays(10));
        bodyProfileRepository.save(profile1);

        BodyProfile profile2 = TestDataFactory.createTestBodyProfile(testUser);
        profile2.setMeasurementDate(LocalDate.now().minusDays(5));
        bodyProfileRepository.save(profile2);

        BodyProfile profile3 = TestDataFactory.createTestBodyProfile(testUser);
        profile3.setMeasurementDate(LocalDate.now());
        bodyProfileRepository.save(profile3);

        // Act & Assert
        mockMvc.perform(get("/api/v1/body-profiles/history")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$.length()").value(3));
    }

    @Test
    @DisplayName("Should get body profile history with limit")
    void shouldGetHistoryWithLimit() throws Exception {
        // Arrange
        for (int i = 0; i < 5; i++) {
            BodyProfile profile = TestDataFactory.createTestBodyProfile(testUser);
            profile.setMeasurementDate(LocalDate.now().minusDays(i));
            bodyProfileRepository.save(profile);
        }

        // Act & Assert
        mockMvc.perform(get("/api/v1/body-profiles/history?limit=2")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    @DisplayName("Should get latest body profile")
    void shouldGetLatestBodyProfile() throws Exception {
        // Arrange
        BodyProfile oldProfile = TestDataFactory.createTestBodyProfile(testUser);
        oldProfile.setMeasurementDate(LocalDate.now().minusDays(10));
        oldProfile.setWeight(BigDecimal.valueOf(70.0));
        bodyProfileRepository.save(oldProfile);

        BodyProfile latestProfile = TestDataFactory.createTestBodyProfile(testUser);
        latestProfile.setMeasurementDate(LocalDate.now());
        latestProfile.setWeight(BigDecimal.valueOf(75.0));
        bodyProfileRepository.save(latestProfile);

        // Act & Assert
        mockMvc.perform(get("/api/v1/body-profiles/latest")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.weight").value(75.0));
    }

    @Test
    @DisplayName("Should return 404 when no body profiles exist")
    void shouldReturn404WhenNoProfilesExist() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/v1/body-profiles/latest")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.message").value("No body profile found for user: " + testUser.getId()));
    }

    @Test
    @DisplayName("Should return empty array when getting history with no profiles")
    void shouldReturnEmptyArrayWhenNoHistory() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/v1/body-profiles/history")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$.length()").value(0));
    }

    @Test
    @DisplayName("Should return 401 without authentication")
    void shouldReturn401WithoutAuth() throws Exception {
        // Arrange
        BodyProfileRequest request = TestDataFactory.createBodyProfileRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/body-profiles")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isUnauthorized());
    }
}
