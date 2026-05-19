package com.gympt.backend.repository;

import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.util.Optional;

import static org.assertj.core.api.Assertions.*;

/**
 * Repository tests for UserRepository.
 * Tests custom query methods and database operations.
 */
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@ActiveProfiles("test")
@DisplayName("UserRepository Tests")
class UserRepositoryTest {

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
    private UserRepository userRepository;

    @Autowired
    private TestEntityManager entityManager;

    @Test
    @DisplayName("Should find user by email")
    void shouldFindUserByEmail() {
        // Arrange
        User user = TestDataFactory.createTestUser("test@example.com", "Test User");
        entityManager.persistAndFlush(user);

        // Act
        Optional<User> foundUser = userRepository.findByEmail("test@example.com");

        // Assert
        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().getEmail()).isEqualTo("test@example.com");
        assertThat(foundUser.get().getName()).isEqualTo("Test User");
    }

    @Test
    @DisplayName("Should return empty when user not found by email")
    void shouldReturnEmptyWhenUserNotFoundByEmail() {
        // Act
        Optional<User> foundUser = userRepository.findByEmail("nonexistent@example.com");

        // Assert
        assertThat(foundUser).isEmpty();
    }

    @Test
    @DisplayName("Should save user successfully")
    void shouldSaveUserSuccessfully() {
        // Arrange
        User user = TestDataFactory.createTestUser("save@example.com", "Save User");

        // Act
        User savedUser = userRepository.save(user);
        entityManager.flush();

        // Assert
        assertThat(savedUser.getId()).isNotNull();
        assertThat(savedUser.getCreatedAt()).isNotNull();
        assertThat(savedUser.getUpdatedAt()).isNotNull();
    }

    @Test
    @DisplayName("Should update user successfully")
    void shouldUpdateUserSuccessfully() {
        // Arrange
        User user = TestDataFactory.createTestUser("update@example.com", "Original Name");
        user = entityManager.persistAndFlush(user);

        // Act
        user.setName("Updated Name");
        user.setAge(35);
        User updatedUser = userRepository.save(user);
        entityManager.flush();

        // Assert
        User foundUser = entityManager.find(User.class, updatedUser.getId());
        assertThat(foundUser.getName()).isEqualTo("Updated Name");
        assertThat(foundUser.getAge()).isEqualTo(35);
    }

    @Test
    @DisplayName("Should delete user successfully")
    void shouldDeleteUserSuccessfully() {
        // Arrange
        User user = TestDataFactory.createTestUser("delete@example.com", "Delete User");
        user = entityManager.persistAndFlush(user);

        // Act
        userRepository.delete(user);
        entityManager.flush();

        // Assert
        User foundUser = entityManager.find(User.class, user.getId());
        assertThat(foundUser).isNull();
    }

    @Test
    @DisplayName("Should enforce unique email constraint")
    void shouldEnforceUniqueEmailConstraint() {
        // Arrange
        User user1 = TestDataFactory.createTestUser("unique@example.com", "User 1");
        entityManager.persistAndFlush(user1);

        User user2 = TestDataFactory.createTestUser("unique@example.com", "User 2");

        // Act & Assert
        assertThatThrownBy(() -> {
            entityManager.persistAndFlush(user2);
        }).isInstanceOf(Exception.class); // Will throw constraint violation
    }

    @Test
    @DisplayName("Should set created and updated timestamps automatically")
    void shouldSetTimestampsAutomatically() {
        // Arrange
        User user = TestDataFactory.createTestUser("timestamp@example.com", "Timestamp User");

        // Act
        User savedUser = userRepository.save(user);
        entityManager.flush();

        // Assert
        assertThat(savedUser.getCreatedAt()).isNotNull();
        assertThat(savedUser.getUpdatedAt()).isNotNull();
        assertThat(savedUser.getCreatedAt()).isEqualTo(savedUser.getUpdatedAt());
    }

    @Test
    @DisplayName("Should update updatedAt timestamp on modification")
    void shouldUpdateTimestampOnModification() throws InterruptedException {
        // Arrange
        User user = TestDataFactory.createTestUser("modified@example.com", "Modified User");
        user = entityManager.persistAndFlush(user);
        var originalUpdatedAt = user.getUpdatedAt();

        // Wait a bit to ensure timestamp difference
        Thread.sleep(100);

        // Act
        user.setName("Modified Name");
        user = userRepository.save(user);
        entityManager.flush();

        // Assert
        assertThat(user.getUpdatedAt()).isAfter(originalUpdatedAt);
    }

    @Test
    @DisplayName("Should find user by ID")
    void shouldFindUserById() {
        // Arrange
        User user = TestDataFactory.createTestUser("findid@example.com", "Find User");
        user = entityManager.persistAndFlush(user);

        // Act
        Optional<User> foundUser = userRepository.findById(user.getId());

        // Assert
        assertThat(foundUser).isPresent();
        assertThat(foundUser.get().getId()).isEqualTo(user.getId());
    }

    @Test
    @DisplayName("Should check if user exists by email")
    void shouldCheckIfUserExistsByEmail() {
        // Arrange
        User user = TestDataFactory.createTestUser("exists@example.com", "Exists User");
        entityManager.persistAndFlush(user);

        // Act
        boolean exists = userRepository.findByEmail("exists@example.com").isPresent();
        boolean notExists = userRepository.findByEmail("notexists@example.com").isPresent();

        // Assert
        assertThat(exists).isTrue();
        assertThat(notExists).isFalse();
    }
}
