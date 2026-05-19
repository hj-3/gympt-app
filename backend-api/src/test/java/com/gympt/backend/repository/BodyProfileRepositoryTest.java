package com.gympt.backend.repository;

import com.gympt.backend.domain.BodyProfile;
import com.gympt.backend.user.User;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.*;

/**
 * Repository tests for BodyProfileRepository.
 * Tests custom query methods, relationships, and pagination.
 */
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@ActiveProfiles("test")
@DisplayName("BodyProfileRepository Tests")
class BodyProfileRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
        DockerImageName.parse("postgres:15-alpine")
    )
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test")
        .withReuse(true);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private BodyProfileRepository bodyProfileRepository;

    @Autowired
    private TestEntityManager entityManager;

    private User testUser;

    @BeforeEach
    void setUp() {
        testUser = TestDataFactory.createTestUser("test@example.com", "Test User");
        testUser = entityManager.persistAndFlush(testUser);
    }

    @Test
    @DisplayName("Should find profiles by user ID ordered by measurement date descending")
    void shouldFindProfilesByUserIdOrderedByDate() {
        // Arrange
        BodyProfile profile1 = TestDataFactory.createTestBodyProfile(testUser);
        profile1.setMeasurementDate(LocalDate.now().minusDays(10));
        entityManager.persistAndFlush(profile1);

        BodyProfile profile2 = TestDataFactory.createTestBodyProfile(testUser);
        profile2.setMeasurementDate(LocalDate.now().minusDays(5));
        entityManager.persistAndFlush(profile2);

        BodyProfile profile3 = TestDataFactory.createTestBodyProfile(testUser);
        profile3.setMeasurementDate(LocalDate.now());
        entityManager.persistAndFlush(profile3);

        // Act
        List<BodyProfile> profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            testUser.getId()
        );

        // Assert
        assertThat(profiles).hasSize(3);
        assertThat(profiles.get(0).getMeasurementDate()).isEqualTo(LocalDate.now());
        assertThat(profiles.get(1).getMeasurementDate()).isEqualTo(LocalDate.now().minusDays(5));
        assertThat(profiles.get(2).getMeasurementDate()).isEqualTo(LocalDate.now().minusDays(10));
    }

    @Test
    @DisplayName("Should find profiles with pagination")
    void shouldFindProfilesWithPagination() {
        // Arrange - Create 5 profiles
        for (int i = 0; i < 5; i++) {
            BodyProfile profile = TestDataFactory.createTestBodyProfile(testUser);
            profile.setMeasurementDate(LocalDate.now().minusDays(i));
            entityManager.persistAndFlush(profile);
        }

        // Act - Get only first 2 profiles
        List<BodyProfile> profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            testUser.getId(),
            PageRequest.of(0, 2)
        );

        // Assert
        assertThat(profiles).hasSize(2);
    }

    @Test
    @DisplayName("Should return empty list when user has no profiles")
    void shouldReturnEmptyListWhenUserHasNoProfiles() {
        // Arrange
        User anotherUser = TestDataFactory.createTestUser("another@example.com", "Another User");
        anotherUser = entityManager.persistAndFlush(anotherUser);

        // Act
        List<BodyProfile> profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            anotherUser.getId()
        );

        // Assert
        assertThat(profiles).isEmpty();
    }

    @Test
    @DisplayName("Should save body profile with user relationship")
    void shouldSaveBodyProfileWithUserRelationship() {
        // Arrange
        BodyProfile profile = TestDataFactory.createTestBodyProfile(testUser);

        // Act
        BodyProfile savedProfile = bodyProfileRepository.save(profile);
        entityManager.flush();

        // Assert
        assertThat(savedProfile.getId()).isNotNull();
        assertThat(savedProfile.getUser()).isNotNull();
        assertThat(savedProfile.getUser().getId()).isEqualTo(testUser.getId());
    }

    @Test
    @DisplayName("Should load user relationship eagerly")
    void shouldLoadUserRelationshipEagerly() {
        // Arrange
        BodyProfile profile = TestDataFactory.createTestBodyProfile(testUser);
        profile = entityManager.persistAndFlush(profile);
        entityManager.clear(); // Clear persistence context

        // Act
        BodyProfile foundProfile = bodyProfileRepository.findById(profile.getId()).orElse(null);

        // Assert
        assertThat(foundProfile).isNotNull();
        assertThat(foundProfile.getUser()).isNotNull();
        assertThat(foundProfile.getUser().getName()).isEqualTo(testUser.getName());
    }

    @Test
    @DisplayName("Should delete body profile without affecting user")
    void shouldDeleteBodyProfileWithoutAffectingUser() {
        // Arrange
        BodyProfile profile = TestDataFactory.createTestBodyProfile(testUser);
        profile = entityManager.persistAndFlush(profile);

        // Act
        bodyProfileRepository.delete(profile);
        entityManager.flush();

        // Assert
        BodyProfile deletedProfile = entityManager.find(BodyProfile.class, profile.getId());
        User user = entityManager.find(User.class, testUser.getId());

        assertThat(deletedProfile).isNull();
        assertThat(user).isNotNull(); // User should still exist
    }

    @Test
    @DisplayName("Should handle multiple profiles for same user")
    void shouldHandleMultipleProfilesForSameUser() {
        // Arrange & Act
        BodyProfile profile1 = TestDataFactory.createTestBodyProfile(testUser);
        profile1.setMeasurementDate(LocalDate.now().minusMonths(2));
        bodyProfileRepository.save(profile1);

        BodyProfile profile2 = TestDataFactory.createTestBodyProfile(testUser);
        profile2.setMeasurementDate(LocalDate.now().minusMonths(1));
        bodyProfileRepository.save(profile2);

        BodyProfile profile3 = TestDataFactory.createTestBodyProfile(testUser);
        profile3.setMeasurementDate(LocalDate.now());
        bodyProfileRepository.save(profile3);

        entityManager.flush();

        // Assert
        List<BodyProfile> profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            testUser.getId()
        );
        assertThat(profiles).hasSize(3);
        assertThat(profiles).extracting(BodyProfile::getUser)
            .allMatch(user -> user.getId().equals(testUser.getId()));
    }

    @Test
    @DisplayName("Should order profiles correctly by measurement date")
    void shouldOrderProfilesCorrectlyByMeasurementDate() {
        // Arrange - Insert profiles out of order
        BodyProfile profile1 = TestDataFactory.createTestBodyProfile(testUser);
        profile1.setMeasurementDate(LocalDate.of(2024, 1, 15));
        entityManager.persistAndFlush(profile1);

        BodyProfile profile2 = TestDataFactory.createTestBodyProfile(testUser);
        profile2.setMeasurementDate(LocalDate.of(2024, 3, 20));
        entityManager.persistAndFlush(profile2);

        BodyProfile profile3 = TestDataFactory.createTestBodyProfile(testUser);
        profile3.setMeasurementDate(LocalDate.of(2024, 2, 10));
        entityManager.persistAndFlush(profile3);

        // Act
        List<BodyProfile> profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            testUser.getId()
        );

        // Assert - Should be ordered: March, February, January
        assertThat(profiles.get(0).getMeasurementDate()).isEqualTo(LocalDate.of(2024, 3, 20));
        assertThat(profiles.get(1).getMeasurementDate()).isEqualTo(LocalDate.of(2024, 2, 10));
        assertThat(profiles.get(2).getMeasurementDate()).isEqualTo(LocalDate.of(2024, 1, 15));
    }

    @Test
    @DisplayName("Should find profiles for specific user only")
    void shouldFindProfilesForSpecificUserOnly() {
        // Arrange
        User user1 = testUser;
        User user2 = TestDataFactory.createTestUser("user2@example.com", "User 2");
        user2 = entityManager.persistAndFlush(user2);

        // Create profiles for both users
        BodyProfile profile1 = TestDataFactory.createTestBodyProfile(user1);
        entityManager.persistAndFlush(profile1);

        BodyProfile profile2 = TestDataFactory.createTestBodyProfile(user2);
        entityManager.persistAndFlush(profile2);

        // Act
        List<BodyProfile> user1Profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            user1.getId()
        );
        List<BodyProfile> user2Profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            user2.getId()
        );

        // Assert
        assertThat(user1Profiles).hasSize(1);
        assertThat(user2Profiles).hasSize(1);
        assertThat(user1Profiles.get(0).getUser().getId()).isEqualTo(user1.getId());
        assertThat(user2Profiles.get(0).getUser().getId()).isEqualTo(user2.getId());
    }
}
