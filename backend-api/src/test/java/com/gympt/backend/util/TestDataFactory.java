package com.gympt.backend.util;

import com.gympt.backend.domain.*;
import com.gympt.backend.dto.*;
import com.gympt.backend.user.User;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

/**
 * Factory class for creating test data entities and DTOs.
 * Provides consistent test data across all test classes.
 */
public class TestDataFactory {

    // User Test Data
    public static User createTestUser() {
        return User.builder()
            .id(UUID.randomUUID())
            .email("test@example.com")
            .password("$2a$10$encoded.password.hash")
            .name("Test User")
            .age(25)
            .gender(User.Gender.MALE)
            .fitnessLevel(User.FitnessLevel.INTERMEDIATE)
            .role(User.Role.USER)
            .status(User.UserStatus.ACTIVE)
            .lastLoginAt(Instant.now())
            .build();
    }

    public static User createTestUser(String email, String name) {
        return User.builder()
            .id(UUID.randomUUID())
            .email(email)
            .password("$2a$10$encoded.password.hash")
            .name(name)
            .age(30)
            .gender(User.Gender.FEMALE)
            .fitnessLevel(User.FitnessLevel.BEGINNER)
            .role(User.Role.USER)
            .status(User.UserStatus.ACTIVE)
            .build();
    }

    public static RegisterRequest createRegisterRequest() {
        return RegisterRequest.builder()
            .email("newuser@example.com")
            .password("Password123!")
            .name("New User")
            .age(28)
            .gender(User.Gender.MALE)
            .fitnessLevel(User.FitnessLevel.BEGINNER)
            .build();
    }

    public static AuthRequest createAuthRequest() {
        return AuthRequest.builder()
            .email("test@example.com")
            .password("Password123!")
            .build();
    }

    public static UserProfileRequest createUserProfileRequest() {
        return UserProfileRequest.builder()
            .name("Updated User")
            .age(26)
            .gender(User.Gender.MALE)
            .fitnessLevel(User.FitnessLevel.ADVANCED)
            .build();
    }

    // BodyProfile Test Data
    public static BodyProfile createTestBodyProfile(User user) {
        return BodyProfile.builder()
            .id(UUID.randomUUID())
            .user(user)
            .height(BigDecimal.valueOf(175.5))
            .weight(BigDecimal.valueOf(70.0))
            .bodyFat(BigDecimal.valueOf(15.5))
            .muscleMass(BigDecimal.valueOf(35.0))
            .postureType(BodyProfile.PostureType.FORWARD_HEAD)
            .measurementDate(LocalDate.now())
            .build();
    }

    public static BodyProfileRequest createBodyProfileRequest() {
        return BodyProfileRequest.builder()
            .height(BigDecimal.valueOf(180.0))
            .weight(BigDecimal.valueOf(75.0))
            .bodyFat(BigDecimal.valueOf(18.0))
            .muscleMass(BigDecimal.valueOf(38.0))
            .postureType(BodyProfile.PostureType.NORMAL)
            .measurementDate(LocalDate.now())
            .build();
    }

    // WorkoutGoal Test Data
    public static WorkoutGoal createTestWorkoutGoal(User user) {
        return WorkoutGoal.builder()
            .id(UUID.randomUUID())
            .user(user)
            .goalType(WorkoutGoal.GoalType.WEIGHT_LOSS)
            .targetValue(BigDecimal.valueOf(10.0))
            .targetDate(LocalDate.now().plusMonths(3))
            .description("Lose 10kg in 3 months")
            .status(WorkoutGoal.GoalStatus.ACTIVE)
            .build();
    }

    public static WorkoutGoalRequest createWorkoutGoalRequest() {
        return WorkoutGoalRequest.builder()
            .goalType(WorkoutGoal.GoalType.MUSCLE_GAIN)
            .targetValue(BigDecimal.valueOf(5.0))
            .targetDate(LocalDate.now().plusMonths(6))
            .description("Gain 5kg muscle mass")
            .build();
    }

    // WorkoutSession Test Data
    public static WorkoutSession createTestWorkoutSession(User user) {
        return WorkoutSession.builder()
            .id(UUID.randomUUID())
            .user(user)
            .startTime(Instant.now())
            .status(WorkoutSession.SessionStatus.IN_PROGRESS)
            .notes("Test workout session")
            .build();
    }

    public static WorkoutSession createCompletedWorkoutSession(User user) {
        return WorkoutSession.builder()
            .id(UUID.randomUUID())
            .user(user)
            .startTime(Instant.now().minusSeconds(3600))
            .endTime(Instant.now())
            .totalDuration(3600)
            .caloriesBurned(500)
            .status(WorkoutSession.SessionStatus.COMPLETED)
            .notes("Completed workout session")
            .build();
    }

    public static WorkoutSessionRequest createWorkoutSessionRequest() {
        return WorkoutSessionRequest.builder()
            .notes("New workout session")
            .build();
    }

    public static EndWorkoutSessionRequest createEndWorkoutSessionRequest() {
        return EndWorkoutSessionRequest.builder()
            .totalDuration(3600)
            .caloriesBurned(450)
            .notes("Great workout!")
            .build();
    }

    // WorkoutPlan Test Data
    public static WorkoutPlan createTestWorkoutPlan(User user) {
        return WorkoutPlan.builder()
            .id(UUID.randomUUID())
            .user(user)
            .name("Test Workout Plan")
            .description("A test workout plan")
            .durationWeeks(8)
            .difficulty(WorkoutPlan.Difficulty.INTERMEDIATE)
            .isActive(true)
            .build();
    }

    // RefreshToken Test Data
    public static RefreshToken createTestRefreshToken(UUID userId, String token) {
        return RefreshToken.builder()
            .id(UUID.randomUUID())
            .userId(userId)
            .token(token)
            .expiresAt(Instant.now().plusSeconds(86400))
            .revoked(false)
            .build();
    }

    public static RefreshToken createExpiredRefreshToken(UUID userId, String token) {
        return RefreshToken.builder()
            .id(UUID.randomUUID())
            .userId(userId)
            .token(token)
            .expiresAt(Instant.now().minusSeconds(3600))
            .revoked(false)
            .build();
    }

    // Report Test Data
    public static Report createTestReport(User user) {
        return Report.builder()
            .id(UUID.randomUUID())
            .userId(user.getId())
            .reportType(Report.ReportType.WORKOUT_SUMMARY)
            .status(Report.ReportStatus.PENDING)
            .generatedAt(Instant.now())
            .build();
    }

    // Storage Test Data
    public static PresignedUrlRequest createPresignedUrlRequest() {
        return PresignedUrlRequest.builder()
            .fileType("workout-videos")
            .fileExtension(".mp4")
            .build();
    }
}
