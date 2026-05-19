package com.gympt.backend.controller;

import com.gympt.backend.BaseIntegrationTest;
import com.gympt.backend.domain.WorkoutGoal;
import com.gympt.backend.dto.WorkoutGoalRequest;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for WorkoutGoalController.
 * Tests workout goal lifecycle operations with authentication.
 */
@DisplayName("WorkoutGoalController Integration Tests")
class WorkoutGoalControllerIntegrationTest extends BaseIntegrationTest {

    @Test
    @DisplayName("Should create workout goal successfully")
    void shouldCreateGoalSuccessfully() throws Exception {
        // Arrange
        WorkoutGoalRequest request = TestDataFactory.createWorkoutGoalRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-goals")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").exists())
            .andExpect(jsonPath("$.goalType").value(request.getGoalType().toString()))
            .andExpect(jsonPath("$.targetValue").value(request.getTargetValue().doubleValue()))
            .andExpect(jsonPath("$.status").value("ACTIVE"));

        // Verify database
        assertThat(workoutGoalRepository.findAll()).hasSize(1);
    }

    @Test
    @DisplayName("Should get all workout goals")
    void shouldGetAllGoals() throws Exception {
        // Arrange
        WorkoutGoal goal1 = TestDataFactory.createTestWorkoutGoal(testUser);
        workoutGoalRepository.save(goal1);

        WorkoutGoal goal2 = TestDataFactory.createTestWorkoutGoal(testUser);
        goal2.setGoalType(WorkoutGoal.GoalType.MUSCLE_GAIN);
        workoutGoalRepository.save(goal2);

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-goals")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    @DisplayName("Should get specific workout goal")
    void shouldGetSpecificGoal() throws Exception {
        // Arrange
        WorkoutGoal goal = TestDataFactory.createTestWorkoutGoal(testUser);
        goal = workoutGoalRepository.save(goal);

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-goals/" + goal.getId())
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(goal.getId().toString()))
            .andExpect(jsonPath("$.goalType").value(goal.getGoalType().toString()));
    }

    @Test
    @DisplayName("Should update goal status to COMPLETED")
    void shouldUpdateGoalStatusToCompleted() throws Exception {
        // Arrange
        WorkoutGoal goal = TestDataFactory.createTestWorkoutGoal(testUser);
        goal = workoutGoalRepository.save(goal);

        // Act & Assert
        mockMvc.perform(patch("/api/v1/workout-goals/" + goal.getId() + "/status")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .param("status", "COMPLETED"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("COMPLETED"));

        // Verify database
        WorkoutGoal updatedGoal = workoutGoalRepository.findById(goal.getId()).orElse(null);
        assertThat(updatedGoal).isNotNull();
        assertThat(updatedGoal.getStatus()).isEqualTo(WorkoutGoal.GoalStatus.COMPLETED);
    }

    @Test
    @DisplayName("Should update goal status to CANCELLED")
    void shouldUpdateGoalStatusToCancelled() throws Exception {
        // Arrange
        WorkoutGoal goal = TestDataFactory.createTestWorkoutGoal(testUser);
        goal = workoutGoalRepository.save(goal);

        // Act & Assert
        mockMvc.perform(patch("/api/v1/workout-goals/" + goal.getId() + "/status")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .param("status", "CANCELLED"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("CANCELLED"));
    }

    @Test
    @DisplayName("Should delete workout goal successfully")
    void shouldDeleteGoalSuccessfully() throws Exception {
        // Arrange
        WorkoutGoal goal = TestDataFactory.createTestWorkoutGoal(testUser);
        goal = workoutGoalRepository.save(goal);

        // Act & Assert
        mockMvc.perform(delete("/api/v1/workout-goals/" + goal.getId())
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNoContent());

        // Verify database
        assertThat(workoutGoalRepository.findById(goal.getId())).isEmpty();
    }

    @Test
    @DisplayName("Should return 404 when getting non-existent goal")
    void shouldReturn404ForNonExistentGoal() throws Exception {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-goals/" + nonExistentId)
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("Should return 404 when deleting non-existent goal")
    void shouldReturn404WhenDeletingNonExistentGoal() throws Exception {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(delete("/api/v1/workout-goals/" + nonExistentId)
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("Should return 401 without authentication")
    void shouldReturn401WithoutAuth() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-goals"))
            .andExpect(status().isUnauthorized());
    }
}
