package com.gympt.backend.service;

import com.gympt.backend.domain.WorkoutGoal;
import com.gympt.backend.dto.WorkoutGoalRequest;
import com.gympt.backend.dto.WorkoutGoalResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.repository.WorkoutGoalRepository;
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
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for WorkoutGoalService.
 * Tests goal creation, retrieval, status updates, and deletion.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("WorkoutGoalService Tests")
class WorkoutGoalServiceTest {

    @Mock
    private WorkoutGoalRepository workoutGoalRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private WorkoutGoalService workoutGoalService;

    private User testUser;
    private UUID testUserId;
    private WorkoutGoal testGoal;
    private UUID testGoalId;

    @BeforeEach
    void setUp() {
        testUser = TestDataFactory.createTestUser();
        testUserId = testUser.getId();
        testGoal = TestDataFactory.createTestWorkoutGoal(testUser);
        testGoalId = testGoal.getId();
    }

    @Test
    @DisplayName("Should create workout goal successfully")
    void shouldCreateGoalSuccessfully() {
        // Arrange
        WorkoutGoalRequest request = TestDataFactory.createWorkoutGoalRequest();
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(workoutGoalRepository.save(any(WorkoutGoal.class)))
            .thenAnswer(invocation -> {
                WorkoutGoal goal = invocation.getArgument(0);
                goal.setId(UUID.randomUUID());
                return goal;
            });

        // Act
        WorkoutGoalResponse response = workoutGoalService.createGoal(testUserId, request);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isNotNull();
        assertThat(response.getGoalType()).isEqualTo(request.getGoalType());
        assertThat(response.getTargetValue()).isEqualTo(request.getTargetValue());
        assertThat(response.getTargetDate()).isEqualTo(request.getTargetDate());
        assertThat(response.getDescription()).isEqualTo(request.getDescription());
        assertThat(response.getStatus()).isEqualTo(WorkoutGoal.GoalStatus.ACTIVE);

        verify(userRepository, times(1)).findById(testUserId);
        verify(workoutGoalRepository, times(1)).save(any(WorkoutGoal.class));
    }

    @Test
    @DisplayName("Should throw exception when creating goal for non-existent user")
    void shouldThrowExceptionWhenCreatingGoalForNonExistentUser() {
        // Arrange
        UUID nonExistentUserId = UUID.randomUUID();
        WorkoutGoalRequest request = TestDataFactory.createWorkoutGoalRequest();
        when(userRepository.findById(nonExistentUserId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutGoalService.createGoal(nonExistentUserId, request))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("User");

        verify(workoutGoalRepository, never()).save(any(WorkoutGoal.class));
    }

    @Test
    @DisplayName("Should get all goals for user")
    void shouldGetAllGoalsForUser() {
        // Arrange
        List<WorkoutGoal> goals = Arrays.asList(
            testGoal,
            TestDataFactory.createTestWorkoutGoal(testUser),
            TestDataFactory.createTestWorkoutGoal(testUser)
        );
        when(workoutGoalRepository.findByUserIdOrderByCreatedAtDesc(testUserId))
            .thenReturn(goals);

        // Act
        List<WorkoutGoalResponse> responses = workoutGoalService.getGoals(testUserId);

        // Assert
        assertThat(responses).hasSize(3);
        verify(workoutGoalRepository, times(1)).findByUserIdOrderByCreatedAtDesc(testUserId);
    }

    @Test
    @DisplayName("Should return empty list when user has no goals")
    void shouldReturnEmptyListWhenUserHasNoGoals() {
        // Arrange
        when(workoutGoalRepository.findByUserIdOrderByCreatedAtDesc(testUserId))
            .thenReturn(Collections.emptyList());

        // Act
        List<WorkoutGoalResponse> responses = workoutGoalService.getGoals(testUserId);

        // Assert
        assertThat(responses).isEmpty();
    }

    @Test
    @DisplayName("Should get specific goal by ID")
    void shouldGetSpecificGoalById() {
        // Arrange
        when(workoutGoalRepository.findById(testGoalId)).thenReturn(Optional.of(testGoal));

        // Act
        WorkoutGoalResponse response = workoutGoalService.getGoal(testGoalId);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isEqualTo(testGoalId);
        assertThat(response.getGoalType()).isEqualTo(testGoal.getGoalType());

        verify(workoutGoalRepository, times(1)).findById(testGoalId);
    }

    @Test
    @DisplayName("Should throw exception when goal not found")
    void shouldThrowExceptionWhenGoalNotFound() {
        // Arrange
        UUID nonExistentGoalId = UUID.randomUUID();
        when(workoutGoalRepository.findById(nonExistentGoalId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutGoalService.getGoal(nonExistentGoalId))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("WorkoutGoal");

        verify(workoutGoalRepository, times(1)).findById(nonExistentGoalId);
    }

    @Test
    @DisplayName("Should update goal status successfully")
    void shouldUpdateGoalStatusSuccessfully() {
        // Arrange
        WorkoutGoal.GoalStatus newStatus = WorkoutGoal.GoalStatus.COMPLETED;
        when(workoutGoalRepository.findById(testGoalId)).thenReturn(Optional.of(testGoal));
        when(workoutGoalRepository.save(any(WorkoutGoal.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        WorkoutGoalResponse response = workoutGoalService.updateGoalStatus(testGoalId, newStatus);

        // Assert
        assertThat(response.getStatus()).isEqualTo(newStatus);
        verify(workoutGoalRepository, times(1)).findById(testGoalId);
        verify(workoutGoalRepository, times(1)).save(testGoal);
    }

    @Test
    @DisplayName("Should update goal status from ACTIVE to COMPLETED")
    void shouldUpdateStatusFromActiveToCompleted() {
        // Arrange
        testGoal.setStatus(WorkoutGoal.GoalStatus.ACTIVE);
        when(workoutGoalRepository.findById(testGoalId)).thenReturn(Optional.of(testGoal));
        when(workoutGoalRepository.save(any(WorkoutGoal.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        WorkoutGoalResponse response = workoutGoalService.updateGoalStatus(
            testGoalId,
            WorkoutGoal.GoalStatus.COMPLETED
        );

        // Assert
        assertThat(response.getStatus()).isEqualTo(WorkoutGoal.GoalStatus.COMPLETED);
    }

    @Test
    @DisplayName("Should update goal status from ACTIVE to CANCELLED")
    void shouldUpdateStatusFromActiveToCancelled() {
        // Arrange
        testGoal.setStatus(WorkoutGoal.GoalStatus.ACTIVE);
        when(workoutGoalRepository.findById(testGoalId)).thenReturn(Optional.of(testGoal));
        when(workoutGoalRepository.save(any(WorkoutGoal.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        WorkoutGoalResponse response = workoutGoalService.updateGoalStatus(
            testGoalId,
            WorkoutGoal.GoalStatus.CANCELLED
        );

        // Assert
        assertThat(response.getStatus()).isEqualTo(WorkoutGoal.GoalStatus.CANCELLED);
    }

    @Test
    @DisplayName("Should throw exception when updating status of non-existent goal")
    void shouldThrowExceptionWhenUpdatingStatusOfNonExistentGoal() {
        // Arrange
        UUID nonExistentGoalId = UUID.randomUUID();
        when(workoutGoalRepository.findById(nonExistentGoalId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutGoalService.updateGoalStatus(
            nonExistentGoalId,
            WorkoutGoal.GoalStatus.COMPLETED
        ))
            .isInstanceOf(ResourceNotFoundException.class);

        verify(workoutGoalRepository, never()).save(any(WorkoutGoal.class));
    }

    @Test
    @DisplayName("Should delete goal successfully")
    void shouldDeleteGoalSuccessfully() {
        // Arrange
        when(workoutGoalRepository.findById(testGoalId)).thenReturn(Optional.of(testGoal));
        doNothing().when(workoutGoalRepository).delete(testGoal);

        // Act
        workoutGoalService.deleteGoal(testGoalId);

        // Assert
        verify(workoutGoalRepository, times(1)).findById(testGoalId);
        verify(workoutGoalRepository, times(1)).delete(testGoal);
    }

    @Test
    @DisplayName("Should throw exception when deleting non-existent goal")
    void shouldThrowExceptionWhenDeletingNonExistentGoal() {
        // Arrange
        UUID nonExistentGoalId = UUID.randomUUID();
        when(workoutGoalRepository.findById(nonExistentGoalId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> workoutGoalService.deleteGoal(nonExistentGoalId))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("WorkoutGoal");

        verify(workoutGoalRepository, never()).delete(any(WorkoutGoal.class));
    }
}
