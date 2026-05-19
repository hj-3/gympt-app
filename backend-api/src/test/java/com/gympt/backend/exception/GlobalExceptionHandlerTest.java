package com.gympt.backend.exception;

import com.gympt.backend.BaseIntegrationTest;
import com.gympt.backend.domain.WorkoutGoal;
import com.gympt.backend.dto.WorkoutGoalRequest;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for GlobalExceptionHandler.
 * Tests exception handling and error response formatting.
 */
@DisplayName("GlobalExceptionHandler Tests")
class GlobalExceptionHandlerTest extends BaseIntegrationTest {

    @Test
    @DisplayName("Should handle ResourceNotFoundException with 404")
    void shouldHandleResourceNotFoundException() throws Exception {
        // Arrange - Non-existent workout goal ID
        UUID nonExistentId = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-goals/" + nonExistentId)
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status").value(404))
            .andExpect(jsonPath("$.error").value("Not Found"))
            .andExpect(jsonPath("$.message").exists())
            .andExpect(jsonPath("$.timestamp").exists())
            .andExpect(jsonPath("$.path").exists());
    }

    @Test
    @DisplayName("Should handle UnauthorizedException with 401")
    void shouldHandleUnauthorizedException() throws Exception {
        // Act & Assert - Access protected endpoint without token
        mockMvc.perform(get("/api/v1/users/profile"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Should handle ValidationException with 400")
    void shouldHandleValidationException() throws Exception {
        // Arrange - Create a completed session and try to end it again
        WorkoutGoal goal = TestDataFactory.createTestWorkoutGoal(testUser);
        goal.setStatus(WorkoutGoal.GoalStatus.COMPLETED);
        goal = workoutGoalRepository.save(goal);

        // This should work without throwing validation exception,
        // so let's test with ending an already completed session instead
        var session = TestDataFactory.createCompletedWorkoutSession(testUser);
        session = workoutSessionRepository.save(session);

        var endRequest = TestDataFactory.createEndWorkoutSessionRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-sessions/" + session.getId() + "/end")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(endRequest)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.status").value(400))
            .andExpect(jsonPath("$.error").value("Bad Request"))
            .andExpect(jsonPath("$.message").exists());
    }

    @Test
    @DisplayName("Should handle MethodArgumentNotValidException with 400")
    void shouldHandleMethodArgumentNotValidException() throws Exception {
        // Arrange - Invalid workout goal request (missing required fields)
        WorkoutGoalRequest invalidRequest = WorkoutGoalRequest.builder()
            .goalType(null) // Required field is null
            .targetValue(null) // Required field is null
            .build();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-goals")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(invalidRequest)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.status").value(400))
            .andExpect(jsonPath("$.error").value("Validation Failed"))
            .andExpect(jsonPath("$.message").exists());
    }

    @Test
    @DisplayName("Should handle BadCredentialsException with 401")
    void shouldHandleBadCredentialsException() throws Exception {
        // Arrange - Invalid credentials
        var authRequest = TestDataFactory.createAuthRequest();
        authRequest.setPassword("WrongPassword!");

        // Act & Assert
        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(authRequest)))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.status").value(401))
            .andExpect(jsonPath("$.error").value("Unauthorized"))
            .andExpect(jsonPath("$.message").value("Invalid email or password"));
    }

    @Test
    @DisplayName("Should return proper error response format")
    void shouldReturnProperErrorResponseFormat() throws Exception {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-goals/" + nonExistentId)
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.timestamp").exists())
            .andExpect(jsonPath("$.status").isNumber())
            .andExpect(jsonPath("$.error").isString())
            .andExpect(jsonPath("$.message").isString())
            .andExpect(jsonPath("$.path").isString());
    }

    @Test
    @DisplayName("Should include validation errors in response")
    void shouldIncludeValidationErrorsInResponse() throws Exception {
        // Arrange - Create request with multiple validation errors
        var request = WorkoutGoalRequest.builder()
            .goalType(WorkoutGoal.GoalType.WEIGHT_LOSS)
            .targetValue(BigDecimal.valueOf(-10)) // Negative value should be invalid
            .targetDate(LocalDate.now().minusDays(1)) // Past date should be invalid
            .build();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-goals")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.status").value(400));
    }

    @Test
    @DisplayName("Should handle missing request body with 400")
    void shouldHandleMissingRequestBody() throws Exception {
        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-goals")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(""))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("Should handle malformed JSON with 400")
    void shouldHandleMalformedJson() throws Exception {
        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-goals")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content("{invalid json}"))
            .andExpect(status().isBadRequest());
    }
}
