# GYMPT Backend API Test Suite

Comprehensive test suite for the GYMPT Backend API built with Spring Boot 3.2.5 and Java 21.

## Overview

This test suite provides comprehensive coverage for:
- Authentication and authorization flows
- User profile management
- Body profile tracking
- Workout goal management
- Workout session lifecycle
- Storage service (S3 integration)
- Event publishing (EventBridge)
- Exception handling
- Repository operations

## Test Structure

```
src/test/java/com/gympt/backend/
├── BaseIntegrationTest.java           # Base class for integration tests
├── auth/
│   ├── JwtTokenProviderTest.java      # JWT token unit tests
│   └── AuthIntegrationTest.java       # Auth flow integration tests
├── controller/
│   ├── UserControllerIntegrationTest.java
│   ├── BodyProfileControllerIntegrationTest.java
│   ├── WorkoutGoalControllerIntegrationTest.java
│   └── WorkoutSessionControllerIntegrationTest.java
├── service/
│   ├── UserServiceTest.java           # Unit tests with mocked dependencies
│   ├── BodyProfileServiceTest.java
│   ├── WorkoutGoalServiceTest.java
│   ├── WorkoutSessionServiceTest.java
│   ├── StorageServiceTest.java
│   └── EventServiceTest.java
├── repository/
│   ├── UserRepositoryTest.java        # Repository tests with @DataJpaTest
│   └── BodyProfileRepositoryTest.java
├── exception/
│   └── GlobalExceptionHandlerTest.java
└── util/
    ├── TestDataFactory.java           # Factory for test data
    └── JwtTestUtil.java               # JWT utilities for tests

src/test/resources/
└── application-test.yml               # Test-specific configuration
```

## Test Categories

### 1. Unit Tests
- **Service Tests**: Test business logic with mocked dependencies
- **JWT Tests**: Token generation and validation
- Focus on individual components in isolation

### 2. Integration Tests
- **Controller Tests**: Full API endpoint testing with MockMvc
- **Auth Flow Tests**: Complete authentication flows
- Use TestContainers for real database
- Test with actual Spring Security configuration

### 3. Repository Tests
- **Data Access Tests**: Test JPA repositories with @DataJpaTest
- Test custom query methods
- Verify entity relationships
- Test cascading operations

## Technology Stack

- **JUnit 5**: Test framework
- **AssertJ**: Fluent assertions
- **Mockito**: Mocking framework
- **TestContainers**: Docker containers for integration tests
  - PostgreSQL 15-alpine
  - Redis 7-alpine
- **Spring Boot Test**: Test utilities and annotations
- **Spring Security Test**: Security testing support
- **MockMvc**: API endpoint testing

## Running Tests

### Run All Tests
```bash
./gradlew test
```

### Run Integration Tests Only
```bash
./gradlew integrationTest
```

### Run Specific Test Class
```bash
./gradlew test --tests UserServiceTest
```

### Run Tests with Coverage
```bash
./gradlew test jacocoTestReport
```
Coverage report: `build/reports/jacoco/test/html/index.html`

### Run Tests in Parallel
Tests are configured to run in parallel for faster execution:
```gradle
maxParallelForks = Runtime.runtime.availableProcessors().intdiv(2) ?: 1
```

## Test Configuration

### TestContainers Setup
```java
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
    .withDatabaseName("gympt_test")
    .withUsername("test")
    .withPassword("test")
    .withReuse(true);

@Container
static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
    .withExposedPorts(6379)
    .withReuse(true);
```

### Base Integration Test
All integration tests extend `BaseIntegrationTest`:
- Automatic TestContainers setup
- Common test data initialization
- Shared repositories and utilities
- Transaction management with `@Transactional`

### Test Data Factory
Consistent test data creation:
```java
User testUser = TestDataFactory.createTestUser();
BodyProfile profile = TestDataFactory.createTestBodyProfile(testUser);
WorkoutGoal goal = TestDataFactory.createTestWorkoutGoal(testUser);
```

### JWT Test Utilities
Generate tokens for authenticated tests:
```java
String accessToken = JwtTestUtil.generateAccessToken(userId);
String refreshToken = JwtTestUtil.generateRefreshToken(userId);
```

## Test Patterns

### AAA Pattern (Arrange-Act-Assert)
All tests follow the AAA pattern:
```java
@Test
void shouldCreateBodyProfileSuccessfully() {
    // Arrange
    BodyProfileRequest request = TestDataFactory.createBodyProfileRequest();
    
    // Act
    BodyProfileResponse response = service.createBodyProfile(userId, request);
    
    // Assert
    assertThat(response).isNotNull();
    assertThat(response.getHeight()).isEqualTo(request.getHeight());
}
```

### Nested Tests
Related tests are grouped with `@Nested`:
```java
@Nested
@DisplayName("Register Tests")
class RegisterTests {
    @Test
    void shouldRegisterSuccessfully() { ... }
    
    @Test
    void shouldRejectDuplicateEmail() { ... }
}
```

### Descriptive Test Names
Tests use descriptive names with `@DisplayName`:
```java
@Test
@DisplayName("Should reject login with wrong password")
void shouldRejectWrongPassword() { ... }
```

## Coverage Goals

- **Target**: 80%+ code coverage
- **Verification**: JaCoCo coverage report
- **Enforcement**: Build fails if coverage < 80%

### Check Coverage
```bash
./gradlew jacocoTestCoverageVerification
```

## Best Practices

### 1. Test Independence
- Each test is independent and can run in isolation
- Use `@BeforeEach` for test data setup
- Clean up data in `BaseIntegrationTest.baseSetUp()`

### 2. Mock External Services
- S3Client is mocked in StorageServiceTest
- EventBridgeClient is mocked in EventServiceTest
- Use LocalStack for local AWS services if needed

### 3. Database State
- Integration tests use `@Transactional` for automatic rollback
- Repository tests use separate TestContainers instance
- Each test starts with clean database state

### 4. Authentication
- Use `testUserAccessToken` from BaseIntegrationTest
- Generate custom tokens with JwtTestUtil
- Test both authenticated and unauthenticated scenarios

### 5. Error Testing
- Test success paths AND failure paths
- Verify exception types and messages
- Test validation errors and constraints

## Common Assertions

### Entity Assertions
```java
assertThat(user).isNotNull();
assertThat(user.getId()).isNotNull();
assertThat(user.getEmail()).isEqualTo("test@example.com");
assertThat(user.getStatus()).isEqualTo(User.UserStatus.ACTIVE);
```

### Collection Assertions
```java
assertThat(profiles).hasSize(3);
assertThat(profiles).isNotEmpty();
assertThat(profiles).extracting(BodyProfile::getHeight)
    .containsExactly(175.0, 180.0, 185.0);
```

### Exception Assertions
```java
assertThatThrownBy(() -> service.getProfile(nonExistentId))
    .isInstanceOf(ResourceNotFoundException.class)
    .hasMessageContaining("User not found");
```

### API Assertions
```java
mockMvc.perform(get("/api/v1/users/profile")
        .header("Authorization", "Bearer " + token))
    .andExpect(status().isOk())
    .andExpect(jsonPath("$.email").value("test@example.com"))
    .andExpect(jsonPath("$.name").exists());
```

## Troubleshooting

### TestContainers Issues
If TestContainers fail to start:
1. Ensure Docker is running
2. Check Docker resource limits (memory, CPU)
3. Use `.withReuse(true)` to reuse containers
4. Check firewall settings for port access

### Slow Tests
To speed up tests:
1. Use container reuse: `.withReuse(true)`
2. Enable parallel execution (already configured)
3. Use `@DataJpaTest` for repository tests
4. Mock external services

### Memory Issues
Increase test heap size in build.gradle:
```gradle
test {
    maxHeapSize = '2g'
}
```

### Port Conflicts
TestContainers uses random ports, but if issues occur:
- Stop other services on common ports (5432, 6379)
- Let TestContainers assign random ports

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:
- Use TestContainers Ryuk for automatic cleanup
- Container reuse disabled in CI (set via env var)
- Parallel execution for faster builds
- JaCoCo reports for coverage tracking

### GitHub Actions Example
```yaml
- name: Run Tests
  run: ./gradlew test jacocoTestReport
  
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: build/reports/jacoco/test/jacocoTestReport.xml
```

## Future Enhancements

- [ ] Add performance tests with JMeter or Gatling
- [ ] Add contract tests with Spring Cloud Contract
- [ ] Add mutation testing with PIT
- [ ] Add security tests with OWASP ZAP
- [ ] Add API documentation tests with Spring REST Docs
- [ ] Add end-to-end tests with Selenium

## Resources

- [JUnit 5 Documentation](https://junit.org/junit5/docs/current/user-guide/)
- [AssertJ Documentation](https://assertj.github.io/doc/)
- [TestContainers Documentation](https://www.testcontainers.org/)
- [Spring Boot Testing](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.testing)
- [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html)
