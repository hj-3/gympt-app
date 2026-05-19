package com.gympt.backend.service;

import com.gympt.backend.domain.WorkoutPlan;
import com.gympt.backend.domain.WorkoutSession;
import com.gympt.backend.dto.EndWorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.exception.ValidationException;
import com.gympt.backend.repository.WorkoutPlanRepository;
import com.gympt.backend.repository.WorkoutSessionRepository;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for WorkoutSessionService.
 * Tests workout session lifecycle: start, end, cancel, and retrieval.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("WorkoutSessionService Tests")
class WorkoutSessionServiceTest {

    @Mock
    private WorkoutSessionRepository workoutSessionRepository;

    @Mock
    private WorkoutPlanRepository workoutPlanRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private WorkoutSessionService workoutSessionService;

    private User testUser;
    private UUID testUserId;
    private WorkoutSession testSession;
    private UUID testSessionId;
    private WorkoutPlan testWorkoutPlan;

    @BeforeEach
    void setUp() {
        testUser = TestDataFactory.createTestUser();
        testUserId = testUser.getId();
        testSession = TestDataFactory.createTestWorkoutSession(testUser);
        testSessionId = testSession.getId();
        testWorkoutPlan = TestDataFactory.createTestWorkoutPlan(testUser);
    }

    @Test
    @DisplayName("Should start workout session successfully")
    void shouldStartSessionSuccessfully() {
        // Arrange
        WorkoutSessionRequest request = TestDataFactory.createWorkoutSessionRequest();
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(workoutSessionRepository.save(any(WorkoutSession.class)))
            .thenAnswer(invocation -> {
                WorkoutSession session = invocation.getArgument(0);
                session.setId(UUID.randomUUID());
                return session;
            });

        // Act
        WorkoutSessionResponse response = workoutSessionService.startSession(testUserId, request);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isNotNull();
        assertThat(response.getStatus()).isEqualTo(WorkoutSession.SessionStatus.IN_PROGRESS);
        assertThat(response.getStartTime()).isNotNull();
        assertThat(response.getNotes()).isEqualTo(request.getNotes());

        verify(userRepository, times(1)).findById(testUserId);
        verify(workoutSessionRepository, times(1)).save(any(WorkoutSession.class));
    }

    @Test
    @DisplayName("Should start session with workout plan")
    void shouldStartSessionWithWorkoutPlan() {
        // Arrange
        WorkoutSessionRequest request = WorkoutSessionRequest.builder()
            .workoutPlanId(testWorkoutPlan.getId())
            .notes("Session with plan")
            .build();

        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(workoutPlanRepository.findById(testWorkoutPlan.getId()))
            .thenReturn(Optional.of(testWorkoutPlan));
        when(workoutSessionRepository.save(any(WorkoutSession.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        WorkoutSessionResponse response = workoutSessionService.startSession(testUserId, request);

        // Assert
        assertThat(response).isNotNull();
        verify(workoutPlanRepository, times(1)).findById(testWorkoutPlan.getId());
    }

    @Test
    @DisplayName("Should throw exception when starting session for non-existent user")
    void shouldThrowExceptionWhenStartingSessionForNonExistentUser() {
        // Arrange
        UUID nonExistentUserId = UUID.randomUUID();
        WorkoutSessionRequest request = TestDataFactory.createWorkoutSessionRequest();
        when(userRepository.findById(nonExistentUserId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.startSession(nonExistentUserId, request))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("User");

        verify(workoutSessionRepository, never()).save(any(WorkoutSession.class));
    }

    @Test
    @DisplayName("Should throw exception when workout plan not found")
    void shouldThrowExceptionWhenWorkoutPlanNotFound() {
        // Arrange
        UUID nonExistentPlanId = UUID.randomUUID();
        WorkoutSessionRequest request = WorkoutSessionRequest.builder()
            .workoutPlanId(nonExistentPlanId)
            .build();

        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(workoutPlanRepository.findById(nonExistentPlanId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.startSession(testUserId, request))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("WorkoutPlan");

        verify(workoutSessionRepository, never()).save(any(WorkoutSession.class));
    }

    @Test
    @DisplayName("Should throw exception when workout plan belongs to different user")
    void shouldThrowExceptionWhenWorkoutPlanBelongsToDifferentUser() {
        // Arrange
        User anotherUser = TestDataFactory.createTestUser("another@example.com", "Another User");
        WorkoutPlan anotherUsersPlan = TestDataFactory.createTestWorkoutPlan(anotherUser);

        WorkoutSessionRequest request = WorkoutSessionRequest.builder()
            .workoutPlanId(anotherUsersPlan.getId())
            .build();

        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(workoutPlanRepository.findById(anotherUsersPlan.getId()))
            .thenReturn(Optional.of(anotherUsersPlan));

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.startSession(testUserId, request))
            .isInstanceOf(ValidationException.class)
            .hasMessageContaining("does not belong to user");

        verify(workoutSessionRepository, never()).save(any(WorkoutSession.class));
    }

    @Test
    @DisplayName("Should end workout session successfully")
    void shouldEndSessionSuccessfully() {
        // Arrange
        EndWorkoutSessionRequest request = TestDataFactory.createEndWorkoutSessionRequest();
        when(workoutSessionRepository.findById(testSessionId)).thenReturn(Optional.of(testSession));
        when(workoutSessionRepository.save(any(WorkoutSession.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        WorkoutSessionResponse response = workoutSessionService.endSession(testSessionId, request);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getStatus()).isEqualTo(WorkoutSession.SessionStatus.COMPLETED);
        assertThat(response.getEndTime()).isNotNull();
        assertThat(response.getTotalDuration()).isEqualTo(request.getTotalDuration());
        assertThat(response.getCaloriesBurned()).isEqualTo(request.getCaloriesBurned());

        verify(workoutSessionRepository, times(1)).findById(testSessionId);
        verify(workoutSessionRepository, times(1)).save(testSession);
    }

    @Test
    @DisplayName("Should throw exception when ending non-existent session")
    void shouldThrowExceptionWhenEndingNonExistentSession() {
        // Arrange
        UUID nonExistentSessionId = UUID.randomUUID();
        EndWorkoutSessionRequest request = TestDataFactory.createEndWorkoutSessionRequest();
        when(workoutSessionRepository.findById(nonExistentSessionId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.endSession(nonExistentSessionId, request))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("WorkoutSession");

        verify(workoutSessionRepository, never()).save(any(WorkoutSession.class));
    }

    @Test
    @DisplayName("Should throw exception when ending non-in-progress session")
    void shouldThrowExceptionWhenEndingNonInProgressSession() {
        // Arrange
        testSession.setStatus(WorkoutSession.SessionStatus.COMPLETED);
        EndWorkoutSessionRequest request = TestDataFactory.createEndWorkoutSessionRequest();
        when(workoutSessionRepository.findById(testSessionId)).thenReturn(Optional.of(testSession));

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.endSession(testSessionId, request))
            .isInstanceOf(ValidationException.class)
            .hasMessageContaining("not in progress");

        verify(workoutSessionRepository, never()).save(any(WorkoutSession.class));
    }

    @Test
    @DisplayName("Should get user sessions")
    void shouldGetUserSessions() {
        // Arrange
        List<WorkoutSession> sessions = Arrays.asList(
            testSession,
            TestDataFactory.createTestWorkoutSession(testUser),
            TestDataFactory.createCompletedWorkoutSession(testUser)
        );
        when(workoutSessionRepository.findByUserIdOrderByStartTimeDesc(testUserId))
            .thenReturn(sessions);

        // Act
        List<WorkoutSessionResponse> responses = workoutSessionService.getUserSessions(testUserId);

        // Assert
        assertThat(responses).hasSize(3);
        verify(workoutSessionRepository, times(1)).findByUserIdOrderByStartTimeDesc(testUserId);
    }

    @Test
    @DisplayName("Should get specific session by ID")
    void shouldGetSessionById() {
        // Arrange
        when(workoutSessionRepository.findById(testSessionId)).thenReturn(Optional.of(testSession));

        // Act
        WorkoutSessionResponse response = workoutSessionService.getSession(testSessionId);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isEqualTo(testSessionId);
        verify(workoutSessionRepository, times(1)).findById(testSessionId);
    }

    @Test
    @DisplayName("Should throw exception when session not found")
    void shouldThrowExceptionWhenSessionNotFound() {
        // Arrange
        UUID nonExistentSessionId = UUID.randomUUID();
        when(workoutSessionRepository.findById(nonExistentSessionId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.getSession(nonExistentSessionId))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("WorkoutSession");
    }

    @Test
    @DisplayName("Should cancel workout session successfully")
    void shouldCancelSessionSuccessfully() {
        // Arrange
        when(workoutSessionRepository.findById(testSessionId)).thenReturn(Optional.of(testSession));
        when(workoutSessionRepository.save(any(WorkoutSession.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        WorkoutSessionResponse response = workoutSessionService.cancelSession(testSessionId);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getStatus()).isEqualTo(WorkoutSession.SessionStatus.CANCELLED);
        assertThat(response.getEndTime()).isNotNull();

        verify(workoutSessionRepository, times(1)).save(testSession);
    }

    @Test
    @DisplayName("Should throw exception when cancelling non-in-progress session")
    void shouldThrowExceptionWhenCancellingNonInProgressSession() {
        // Arrange
        testSession.setStatus(WorkoutSession.SessionStatus.COMPLETED);
        when(workoutSessionRepository.findById(testSessionId)).thenReturn(Optional.of(testSession));

        // Act & Assert
        assertThatThrownBy(() -> workoutSessionService.cancelSession(testSessionId))
            .isInstanceOf(ValidationException.class)
            .hasMessageContaining("Only in-progress sessions can be cancelled");

        verify(workoutSessionRepository, never()).save(any(WorkoutSession.class));
    }
}
