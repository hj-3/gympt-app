package com.gympt.backend.controller;

import com.gympt.backend.BaseIntegrationTest;
import com.gympt.backend.dto.UserProfileRequest;
import com.gympt.backend.user.User;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for UserController.
 * Tests user profile CRUD operations with authentication.
 */
@DisplayName("UserController Integration Tests")
class UserControllerIntegrationTest extends BaseIntegrationTest {

    @Test
    @DisplayName("Should get user profile successfully")
    void shouldGetProfileSuccessfully() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/v1/users/profile")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value(testUser.getEmail()))
            .andExpect(jsonPath("$.name").value(testUser.getName()))
            .andExpect(jsonPath("$.age").value(testUser.getAge()))
            .andExpect(jsonPath("$.gender").value(testUser.getGender().toString()))
            .andExpect(jsonPath("$.fitnessLevel").value(testUser.getFitnessLevel().toString()));
    }

    @Test
    @DisplayName("Should return 401 when accessing profile without token")
    void shouldReturn401WithoutToken() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/v1/users/profile"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Should update user profile successfully")
    void shouldUpdateProfileSuccessfully() throws Exception {
        // Arrange
        UserProfileRequest request = UserProfileRequest.builder()
            .name("Updated Name")
            .age(35)
            .gender(User.Gender.MALE)
            .fitnessLevel(User.FitnessLevel.ADVANCED)
            .build();

        // Act & Assert
        mockMvc.perform(put("/api/v1/users/profile")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Updated Name"))
            .andExpect(jsonPath("$.age").value(35))
            .andExpect(jsonPath("$.fitnessLevel").value("ADVANCED"));

        // Verify database was updated
        User updatedUser = userRepository.findById(testUser.getId()).orElse(null);
        assertThat(updatedUser).isNotNull();
        assertThat(updatedUser.getName()).isEqualTo("Updated Name");
        assertThat(updatedUser.getAge()).isEqualTo(35);
    }

    @Test
    @DisplayName("Should update profile with partial data")
    void shouldUpdateProfileWithPartialData() throws Exception {
        // Arrange
        String originalName = testUser.getName();
        Integer originalAge = testUser.getAge();

        UserProfileRequest request = UserProfileRequest.builder()
            .name("Only Name Updated")
            .build();

        // Act & Assert
        mockMvc.perform(put("/api/v1/users/profile")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Only Name Updated"))
            .andExpect(jsonPath("$.age").value(originalAge));
    }

    @Test
    @DisplayName("Should delete account successfully with soft delete")
    void shouldDeleteAccountSuccessfully() throws Exception {
        // Act & Assert
        mockMvc.perform(delete("/api/v1/users/profile")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNoContent());

        // Verify soft delete
        User deletedUser = userRepository.findById(testUser.getId()).orElse(null);
        assertThat(deletedUser).isNotNull();
        assertThat(deletedUser.getStatus()).isEqualTo(User.UserStatus.DELETED);

        // Verify refresh tokens were deleted
        assertThat(refreshTokenRepository.findByUserId(testUser.getId())).isEmpty();
    }

    @Test
    @DisplayName("Should return 401 when deleting account without token")
    void shouldReturn401WhenDeletingWithoutToken() throws Exception {
        // Act & Assert
        mockMvc.perform(delete("/api/v1/users/profile"))
            .andExpect(status().isUnauthorized());

        // Verify account was not deleted
        User user = userRepository.findById(testUser.getId()).orElse(null);
        assertThat(user).isNotNull();
        assertThat(user.getStatus()).isEqualTo(User.UserStatus.ACTIVE);
    }

    @Test
    @DisplayName("Should validate profile update request")
    void shouldValidateProfileUpdateRequest() throws Exception {
        // Arrange - Invalid age (negative)
        UserProfileRequest request = UserProfileRequest.builder()
            .name("Valid Name")
            .age(-1)
            .build();

        // Act & Assert
        mockMvc.perform(put("/api/v1/users/profile")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }
}
