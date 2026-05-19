package com.gympt.backend.service;

import com.gympt.backend.dto.UserProfileRequest;
import com.gympt.backend.dto.UserProfileResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.repository.RefreshTokenRepository;
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

import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for UserService.
 * Tests user profile operations with mocked dependencies.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("UserService Tests")
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private RefreshTokenRepository refreshTokenRepository;

    @InjectMocks
    private UserService userService;

    private User testUser;
    private UUID testUserId;

    @BeforeEach
    void setUp() {
        testUser = TestDataFactory.createTestUser();
        testUserId = testUser.getId();
    }

    @Test
    @DisplayName("Should get user profile successfully")
    void shouldGetProfileSuccessfully() {
        // Arrange
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));

        // Act
        UserProfileResponse response = userService.getProfile(testUserId);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getEmail()).isEqualTo(testUser.getEmail());
        assertThat(response.getName()).isEqualTo(testUser.getName());
        assertThat(response.getAge()).isEqualTo(testUser.getAge());
        assertThat(response.getGender()).isEqualTo(testUser.getGender());
        assertThat(response.getFitnessLevel()).isEqualTo(testUser.getFitnessLevel());

        verify(userRepository, times(1)).findById(testUserId);
    }

    @Test
    @DisplayName("Should throw ResourceNotFoundException when user not found")
    void shouldThrowExceptionWhenUserNotFound() {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();
        when(userRepository.findById(nonExistentId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> userService.getProfile(nonExistentId))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("User")
            .hasMessageContaining(nonExistentId.toString());

        verify(userRepository, times(1)).findById(nonExistentId);
    }

    @Test
    @DisplayName("Should update user profile successfully")
    void shouldUpdateProfileSuccessfully() {
        // Arrange
        UserProfileRequest request = UserProfileRequest.builder()
            .name("Updated Name")
            .age(30)
            .gender(User.Gender.MALE)
            .fitnessLevel(User.FitnessLevel.ADVANCED)
            .build();

        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        UserProfileResponse response = userService.updateProfile(testUserId, request);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getName()).isEqualTo("Updated Name");
        assertThat(response.getAge()).isEqualTo(30);
        assertThat(response.getGender()).isEqualTo(User.Gender.MALE);
        assertThat(response.getFitnessLevel()).isEqualTo(User.FitnessLevel.ADVANCED);

        verify(userRepository, times(1)).findById(testUserId);
        verify(userRepository, times(1)).save(testUser);
    }

    @Test
    @DisplayName("Should update profile with partial data")
    void shouldUpdateProfileWithPartialData() {
        // Arrange
        UserProfileRequest request = UserProfileRequest.builder()
            .name("New Name")
            .build();

        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        UserProfileResponse response = userService.updateProfile(testUserId, request);

        // Assert
        assertThat(response.getName()).isEqualTo("New Name");
        assertThat(response.getAge()).isEqualTo(testUser.getAge()); // Unchanged
        assertThat(response.getGender()).isEqualTo(testUser.getGender()); // Unchanged

        verify(userRepository, times(1)).save(testUser);
    }

    @Test
    @DisplayName("Should throw exception when updating non-existent user")
    void shouldThrowExceptionWhenUpdatingNonExistentUser() {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();
        UserProfileRequest request = TestDataFactory.createUserProfileRequest();
        when(userRepository.findById(nonExistentId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> userService.updateProfile(nonExistentId, request))
            .isInstanceOf(ResourceNotFoundException.class);

        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    @DisplayName("Should delete account successfully with soft delete")
    void shouldDeleteAccountSuccessfully() {
        // Arrange
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        userService.deleteAccount(testUserId);

        // Assert
        assertThat(testUser.getStatus()).isEqualTo(User.UserStatus.DELETED);
        verify(userRepository, times(1)).findById(testUserId);
        verify(userRepository, times(1)).save(testUser);
        verify(refreshTokenRepository, times(1)).deleteByUserId(testUserId);
    }

    @Test
    @DisplayName("Should throw exception when deleting non-existent account")
    void shouldThrowExceptionWhenDeletingNonExistentAccount() {
        // Arrange
        UUID nonExistentId = UUID.randomUUID();
        when(userRepository.findById(nonExistentId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> userService.deleteAccount(nonExistentId))
            .isInstanceOf(ResourceNotFoundException.class);

        verify(userRepository, never()).save(any(User.class));
        verify(refreshTokenRepository, never()).deleteByUserId(any(UUID.class));
    }

    @Test
    @DisplayName("Should handle already deleted account")
    void shouldHandleAlreadyDeletedAccount() {
        // Arrange
        testUser.setStatus(User.UserStatus.DELETED);
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        userService.deleteAccount(testUserId);

        // Assert
        assertThat(testUser.getStatus()).isEqualTo(User.UserStatus.DELETED);
        verify(userRepository, times(1)).save(testUser);
        verify(refreshTokenRepository, times(1)).deleteByUserId(testUserId);
    }
}
