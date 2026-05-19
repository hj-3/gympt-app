package com.gympt.backend.service;

import com.gympt.backend.domain.BodyProfile;
import com.gympt.backend.dto.BodyProfileRequest;
import com.gympt.backend.dto.BodyProfileResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.repository.BodyProfileRepository;
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
import org.springframework.data.domain.PageRequest;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

/**
 * Unit tests for BodyProfileService.
 * Tests body profile creation, history retrieval, and latest profile operations.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("BodyProfileService Tests")
class BodyProfileServiceTest {

    @Mock
    private BodyProfileRepository bodyProfileRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private BodyProfileService bodyProfileService;

    private User testUser;
    private UUID testUserId;
    private BodyProfile testBodyProfile;

    @BeforeEach
    void setUp() {
        testUser = TestDataFactory.createTestUser();
        testUserId = testUser.getId();
        testBodyProfile = TestDataFactory.createTestBodyProfile(testUser);
    }

    @Test
    @DisplayName("Should create body profile successfully")
    void shouldCreateBodyProfileSuccessfully() {
        // Arrange
        BodyProfileRequest request = TestDataFactory.createBodyProfileRequest();
        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(bodyProfileRepository.save(any(BodyProfile.class)))
            .thenAnswer(invocation -> {
                BodyProfile profile = invocation.getArgument(0);
                profile.setId(UUID.randomUUID());
                return profile;
            });

        // Act
        BodyProfileResponse response = bodyProfileService.createBodyProfile(testUserId, request);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isNotNull();
        assertThat(response.getHeight()).isEqualTo(request.getHeight());
        assertThat(response.getWeight()).isEqualTo(request.getWeight());
        assertThat(response.getBodyFat()).isEqualTo(request.getBodyFat());
        assertThat(response.getMuscleMass()).isEqualTo(request.getMuscleMass());
        assertThat(response.getPostureType()).isEqualTo(request.getPostureType());

        verify(userRepository, times(1)).findById(testUserId);
        verify(bodyProfileRepository, times(1)).save(any(BodyProfile.class));
    }

    @Test
    @DisplayName("Should throw exception when creating profile for non-existent user")
    void shouldThrowExceptionWhenCreatingProfileForNonExistentUser() {
        // Arrange
        UUID nonExistentUserId = UUID.randomUUID();
        BodyProfileRequest request = TestDataFactory.createBodyProfileRequest();
        when(userRepository.findById(nonExistentUserId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> bodyProfileService.createBodyProfile(nonExistentUserId, request))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("User");

        verify(bodyProfileRepository, never()).save(any(BodyProfile.class));
    }

    @Test
    @DisplayName("Should create body profile with valid measurements")
    void shouldCreateBodyProfileWithValidMeasurements() {
        // Arrange
        BodyProfileRequest request = BodyProfileRequest.builder()
            .height(BigDecimal.valueOf(185.0))
            .weight(BigDecimal.valueOf(80.0))
            .bodyFat(BigDecimal.valueOf(12.5))
            .muscleMass(BigDecimal.valueOf(40.0))
            .postureType(BodyProfile.PostureType.ROUNDED_SHOULDERS)
            .measurementDate(LocalDate.now())
            .build();

        when(userRepository.findById(testUserId)).thenReturn(Optional.of(testUser));
        when(bodyProfileRepository.save(any(BodyProfile.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // Act
        BodyProfileResponse response = bodyProfileService.createBodyProfile(testUserId, request);

        // Assert
        assertThat(response.getHeight()).isEqualByComparingTo(BigDecimal.valueOf(185.0));
        assertThat(response.getWeight()).isEqualByComparingTo(BigDecimal.valueOf(80.0));
        assertThat(response.getBodyFat()).isEqualByComparingTo(BigDecimal.valueOf(12.5));
    }

    @Test
    @DisplayName("Should get history with limit")
    void shouldGetHistoryWithLimit() {
        // Arrange
        List<BodyProfile> profiles = Arrays.asList(
            testBodyProfile,
            TestDataFactory.createTestBodyProfile(testUser),
            TestDataFactory.createTestBodyProfile(testUser)
        );
        int limit = 2;

        when(bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            eq(testUserId),
            eq(PageRequest.of(0, limit))
        )).thenReturn(profiles.subList(0, limit));

        // Act
        List<BodyProfileResponse> responses = bodyProfileService.getHistory(testUserId, limit);

        // Assert
        assertThat(responses).hasSize(2);
        verify(bodyProfileRepository, times(1))
            .findByUserIdOrderByMeasurementDateDesc(eq(testUserId), eq(PageRequest.of(0, limit)));
    }

    @Test
    @DisplayName("Should get history without limit")
    void shouldGetHistoryWithoutLimit() {
        // Arrange
        List<BodyProfile> profiles = Arrays.asList(
            testBodyProfile,
            TestDataFactory.createTestBodyProfile(testUser)
        );

        when(bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(testUserId))
            .thenReturn(profiles);

        // Act
        List<BodyProfileResponse> responses = bodyProfileService.getHistory(testUserId, null);

        // Assert
        assertThat(responses).hasSize(2);
        verify(bodyProfileRepository, times(1))
            .findByUserIdOrderByMeasurementDateDesc(testUserId);
    }

    @Test
    @DisplayName("Should return empty history when no profiles exist")
    void shouldReturnEmptyHistoryWhenNoProfiles() {
        // Arrange
        when(bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(testUserId))
            .thenReturn(Collections.emptyList());

        // Act
        List<BodyProfileResponse> responses = bodyProfileService.getHistory(testUserId, null);

        // Assert
        assertThat(responses).isEmpty();
    }

    @Test
    @DisplayName("Should get latest body profile successfully")
    void shouldGetLatestBodyProfileSuccessfully() {
        // Arrange
        when(bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            eq(testUserId),
            eq(PageRequest.of(0, 1))
        )).thenReturn(Collections.singletonList(testBodyProfile));

        // Act
        BodyProfileResponse response = bodyProfileService.getLatest(testUserId);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isEqualTo(testBodyProfile.getId());
        assertThat(response.getHeight()).isEqualTo(testBodyProfile.getHeight());

        verify(bodyProfileRepository, times(1))
            .findByUserIdOrderByMeasurementDateDesc(eq(testUserId), eq(PageRequest.of(0, 1)));
    }

    @Test
    @DisplayName("Should throw exception when no body profile exists")
    void shouldThrowExceptionWhenNoBodyProfileExists() {
        // Arrange
        when(bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            eq(testUserId),
            eq(PageRequest.of(0, 1))
        )).thenReturn(Collections.emptyList());

        // Act & Assert
        assertThatThrownBy(() -> bodyProfileService.getLatest(testUserId))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("No body profile found");
    }

    @Test
    @DisplayName("Should handle pagination correctly")
    void shouldHandlePaginationCorrectly() {
        // Arrange
        List<BodyProfile> profiles = Arrays.asList(
            TestDataFactory.createTestBodyProfile(testUser),
            TestDataFactory.createTestBodyProfile(testUser),
            TestDataFactory.createTestBodyProfile(testUser)
        );
        int limit = 5;

        when(bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            eq(testUserId),
            eq(PageRequest.of(0, limit))
        )).thenReturn(profiles);

        // Act
        List<BodyProfileResponse> responses = bodyProfileService.getHistory(testUserId, limit);

        // Assert
        assertThat(responses).hasSize(3);
    }
}
