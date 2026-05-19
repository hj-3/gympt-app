package com.gympt.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gympt.backend.auth.JwtTokenProvider;
import com.gympt.backend.repository.*;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import com.gympt.backend.util.JwtTestUtil;
import com.gympt.backend.util.TestDataFactory;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.util.UUID;

/**
 * Base class for integration tests.
 * Provides TestContainers setup for PostgreSQL and Redis,
 * common test utilities, and shared test data setup.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
@Testcontainers
@ActiveProfiles("test")
@Transactional
@Tag("integration")
public abstract class BaseIntegrationTest {

    @Container
    protected static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
        DockerImageName.parse("postgres:15-alpine")
    )
        .withDatabaseName("gympt_test")
        .withUsername("test")
        .withPassword("test")
        .withReuse(true);

    @Container
    protected static GenericContainer<?> redis = new GenericContainer<>(
        DockerImageName.parse("redis:7-alpine")
    )
        .withExposedPorts(6379)
        .withReuse(true);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", redis::getFirstMappedPort);
    }

    @LocalServerPort
    protected int port;

    @Autowired
    protected MockMvc mockMvc;

    @Autowired
    protected ObjectMapper objectMapper;

    @Autowired
    protected JwtTokenProvider jwtTokenProvider;

    @Autowired
    protected PasswordEncoder passwordEncoder;

    // Repositories
    @Autowired
    protected UserRepository userRepository;

    @Autowired
    protected RefreshTokenRepository refreshTokenRepository;

    @Autowired
    protected BodyProfileRepository bodyProfileRepository;

    @Autowired
    protected WorkoutGoalRepository workoutGoalRepository;

    @Autowired
    protected WorkoutSessionRepository workoutSessionRepository;

    @Autowired
    protected WorkoutPlanRepository workoutPlanRepository;

    @Autowired
    protected ReportRepository reportRepository;

    protected User testUser;
    protected String testUserAccessToken;
    protected String testUserRefreshToken;

    @BeforeEach
    void baseSetUp() {
        // Clean up all repositories
        workoutSessionRepository.deleteAll();
        workoutGoalRepository.deleteAll();
        bodyProfileRepository.deleteAll();
        workoutPlanRepository.deleteAll();
        reportRepository.deleteAll();
        refreshTokenRepository.deleteAll();
        userRepository.deleteAll();

        // Create test user
        testUser = createAndSaveTestUser("test@example.com", "Test User");
        testUserAccessToken = JwtTestUtil.generateAccessToken(testUser.getId());
        testUserRefreshToken = JwtTestUtil.generateRefreshToken(testUser.getId());
    }

    /**
     * Create and save a test user with encoded password.
     */
    protected User createAndSaveTestUser(String email, String name) {
        User user = TestDataFactory.createTestUser(email, name);
        user.setPassword(passwordEncoder.encode("Password123!"));
        return userRepository.save(user);
    }

    /**
     * Create and save a test user with custom attributes.
     */
    protected User createAndSaveTestUser(String email, String name, User.Role role, User.UserStatus status) {
        User user = TestDataFactory.createTestUser(email, name);
        user.setPassword(passwordEncoder.encode("Password123!"));
        user.setRole(role);
        user.setStatus(status);
        return userRepository.save(user);
    }

    /**
     * Generate an access token for the given user.
     */
    protected String generateAccessToken(User user) {
        return JwtTestUtil.generateAccessToken(user.getId());
    }

    /**
     * Generate a refresh token for the given user.
     */
    protected String generateRefreshToken(User user) {
        return JwtTestUtil.generateRefreshToken(user.getId());
    }

    /**
     * Get base URL for API calls.
     */
    protected String getBaseUrl() {
        return "http://localhost:" + port;
    }

    /**
     * Get API endpoint URL.
     */
    protected String getApiUrl(String endpoint) {
        return getBaseUrl() + "/api/v1" + endpoint;
    }
}
