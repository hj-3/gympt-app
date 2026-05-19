package com.gympt.backend.controller;

import com.gympt.backend.BaseIntegrationTest;
import com.gympt.backend.domain.WorkoutSession;
import com.gympt.backend.dto.EndWorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionRequest;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for WorkoutSessionController.
 * Tests workout session lifecycle: start, end, cancel operations.
 */
@DisplayName("WorkoutSessionController Integration Tests")
class WorkoutSessionControllerIntegrationTest extends BaseIntegrationTest {

    @Test
    @DisplayName("Should start workout session successfully")
    void shouldStartSessionSuccessfully() throws Exception {
        // Arrange
        WorkoutSessionRequest request = TestDataFactory.createWorkoutSessionRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-sessions")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").exists())
            .andExpect(jsonPath("$.status").value("IN_PROGRESS"))
            .andExpect(jsonPath("$.startTime").exists())
            .andExpect(jsonPath("$.notes").value(request.getNotes()));

        // Verify database
        assertThat(workoutSessionRepository.findAll()).hasSize(1);
    }

    @Test
    @DisplayName("Should end workout session successfully")
    void shouldEndSessionSuccessfully() throws Exception {
        // Arrange
        WorkoutSession session = TestDataFactory.createTestWorkoutSession(testUser);
        session = workoutSessionRepository.save(session);

        EndWorkoutSessionRequest request = TestDataFactory.createEndWorkoutSessionRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-sessions/" + session.getId() + "/end")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("COMPLETED"))
            .andExpect(jsonPath("$.endTime").exists())
            .andExpect(jsonPath("$.totalDuration").value(request.getTotalDuration()))
            .andExpect(jsonPath("$.caloriesBurned").value(request.getCaloriesBurned()));

        // Verify database
        WorkoutSession endedSession = workoutSessionRepository.findById(session.getId()).orElse(null);
        assertThat(endedSession).isNotNull();
        assertThat(endedSession.getStatus()).isEqualTo(WorkoutSession.SessionStatus.COMPLETED);
        assertThat(endedSession.getEndTime()).isNotNull();
    }

    @Test
    @DisplayName("Should cancel workout session successfully")
    void shouldCancelSessionSuccessfully() throws Exception {
        // Arrange
        WorkoutSession session = TestDataFactory.createTestWorkoutSession(testUser);
        session = workoutSessionRepository.save(session);

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-sessions/" + session.getId() + "/cancel")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("CANCELLED"))
            .andExpect(jsonPath("$.endTime").exists());

        // Verify database
        WorkoutSession cancelledSession = workoutSessionRepository.findById(session.getId()).orElse(null);
        assertThat(cancelledSession).isNotNull();
        assertThat(cancelledSession.getStatus()).isEqualTo(WorkoutSession.SessionStatus.CANCELLED);
    }

    @Test
    @DisplayName("Should get all user workout sessions")
    void shouldGetAllUserSessions() throws Exception {
        // Arrange
        WorkoutSession session1 = TestDataFactory.createTestWorkoutSession(testUser);
        workoutSessionRepository.save(session1);

        WorkoutSession session2 = TestDataFactory.createCompletedWorkoutSession(testUser);
        workoutSessionRepository.save(session2);

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-sessions")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    @DisplayName("Should get specific workout session")
    void shouldGetSpecificSession() throws Exception {
        // Arrange
        WorkoutSession session = TestDataFactory.createTestWorkoutSession(testUser);
        session = workoutSessionRepository.save(session);

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-sessions/" + session.getId())
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(session.getId().toString()))
            .andExpect(jsonPath("$.status").value("IN_PROGRESS"));
    }

    @Test
    @DisplayName("Should return 400 when ending non-in-progress session")
    void shouldReturn400WhenEndingNonInProgressSession() throws Exception {
        // Arrange
        WorkoutSession session = TestDataFactory.createCompletedWorkoutSession(testUser);
        session = workoutSessionRepository.save(session);

        EndWorkoutSessionRequest request = TestDataFactory.createEndWorkoutSessionRequest();

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-sessions/" + session.getId() + "/end")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.message").value("Workout session is not in progress"));
    }

    @Test
    @DisplayName("Should return 400 when cancelling non-in-progress session")
    void shouldReturn400WhenCancellingNonInProgressSession() throws Exception {
        // Arrange
        WorkoutSession session = TestDataFactory.createCompletedWorkoutSession(testUser);
        session = workoutSessionRepository.save(session);

        // Act & Assert
        mockMvc.perform(post("/api/v1/workout-sessions/" + session.getId() + "/cancel")
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.message").value("Only in-progress sessions can be cancelled"));
    }

    @Test
    @DisplayName("Should return 404 when getting non-existent session")
    void shouldReturn404ForNonExistentSession() throws Exception {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-sessions/" + nonExistentId)
                .header("Authorization", "Bearer " + testUserAccessToken))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("Should return 401 without authentication")
    void shouldReturn401WithoutAuth() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/v1/workout-sessions"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Should handle multiple concurrent sessions")
    void shouldHandleMultipleConcurrentSessions() throws Exception {
        // Arrange & Act
        WorkoutSessionRequest request1 = TestDataFactory.createWorkoutSessionRequest();
        request1.setNotes("Session 1");

        WorkoutSessionRequest request2 = TestDataFactory.createWorkoutSessionRequest();
        request2.setNotes("Session 2");

        // Start two sessions
        mockMvc.perform(post("/api/v1/workout-sessions")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request1)))
            .andExpect(status().isCreated());

        mockMvc.perform(post("/api/v1/workout-sessions")
                .header("Authorization", "Bearer " + testUserAccessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request2)))
            .andExpect(status().isCreated());

        // Assert - Both sessions should exist
        assertThat(workoutSessionRepository.findAll()).hasSize(2);
    }
}
