# Backend API - Testing Guide

## Testing Strategy

### Test Pyramid

```
        /\
       /  \      E2E Tests (5%)
      /----\     
     /      \    Integration Tests (25%)
    /--------\   
   /          \  Unit Tests (70%)
  /____________\ 
```

### Coverage Goals

- **Overall Coverage:** > 80%
- **Business Logic:** > 90%
- **Controllers:** > 70%
- **Critical Paths:** 100%

---

## Unit Tests

### Location
`src/test/java/com/gympt/api/unit/`

### Framework
- **JUnit 5** - Test framework
- **Mockito** - Mocking framework
- **AssertJ** - Fluent assertions

### Example: Service Unit Test

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private PasswordEncoder passwordEncoder;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    @DisplayName("Should create user successfully")
    void shouldCreateUser() {
        // Arrange
        CreateUserRequest request = new CreateUserRequest(
            "test@example.com",
            "password123",
            "Test User"
        );
        
        User expectedUser = User.builder()
            .id(UUID.randomUUID())
            .email(request.getEmail())
            .name(request.getName())
            .build();
        
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(false);
        when(passwordEncoder.encode(request.getPassword())).thenReturn("encoded");
        when(userRepository.save(any(User.class))).thenReturn(expectedUser);
        
        // Act
        User result = userService.createUser(request);
        
        // Assert
        assertThat(result).isNotNull();
        assertThat(result.getEmail()).isEqualTo(request.getEmail());
        verify(userRepository).save(any(User.class));
    }
    
    @Test
    @DisplayName("Should throw exception when email already exists")
    void shouldThrowExceptionWhenEmailExists() {
        // Arrange
        CreateUserRequest request = new CreateUserRequest(
            "existing@example.com",
            "password123",
            "Test User"
        );
        
        when(userRepository.existsByEmail(request.getEmail())).thenReturn(true);
        
        // Act & Assert
        assertThatThrownBy(() -> userService.createUser(request))
            .isInstanceOf(EmailAlreadyExistsException.class)
            .hasMessage("Email already exists: existing@example.com");
    }
}
```

### Running Unit Tests

```bash
# Run all unit tests
./gradlew test

# Run specific test class
./gradlew test --tests UserServiceTest

# Run with coverage
./gradlew test jacocoTestReport

# View coverage report
open build/reports/jacoco/test/html/index.html
```

---

## Integration Tests

### Location
`src/test/java/com/gympt/api/integration/`

### Framework
- **Spring Boot Test** - Spring context
- **TestContainers** - Docker containers for dependencies
- **RestAssured** - API testing
- **WireMock** - External service mocking

### Example: API Integration Test

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class UserControllerIntegrationTest {
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("gympt_test")
        .withUsername("test")
        .withPassword("test");
    
    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);
    
    @LocalServerPort
    private int port;
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @Autowired
    private UserRepository userRepository;
    
    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }
    
    @Test
    @DisplayName("Should register new user")
    void shouldRegisterNewUser() {
        // Arrange
        RegisterRequest request = new RegisterRequest(
            "newuser@example.com",
            "SecureP@ss123",
            "New User",
            30,
            "male"
        );
        
        // Act
        ResponseEntity<RegisterResponse> response = restTemplate.postForEntity(
            "/api/v1/auth/register",
            request,
            RegisterResponse.class
        );
        
        // Assert
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getEmail()).isEqualTo(request.getEmail());
        assertThat(response.getBody().getAccessToken()).isNotBlank();
        
        // Verify database
        Optional<User> savedUser = userRepository.findByEmail(request.getEmail());
        assertThat(savedUser).isPresent();
    }
    
    @Test
    @DisplayName("Should return 409 when email already exists")
    void shouldReturn409WhenEmailExists() {
        // Arrange
        User existingUser = userRepository.save(User.builder()
            .email("existing@example.com")
            .password("encoded")
            .name("Existing")
            .build());
        
        RegisterRequest request = new RegisterRequest(
            "existing@example.com",
            "password",
            "Duplicate",
            25,
            "female"
        );
        
        // Act
        ResponseEntity<ErrorResponse> response = restTemplate.postForEntity(
            "/api/v1/auth/register",
            request,
            ErrorResponse.class
        );
        
        // Assert
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
    }
}
```

### Running Integration Tests

```bash
# Run all integration tests
./gradlew integrationTest

# Run specific test
./gradlew integrationTest --tests UserControllerIntegrationTest

# Run with TestContainers logs
./gradlew integrationTest -i
```

---

## Contract Tests

### Testing External Service Contracts

Use WireMock to mock external services:

```java
@WireMockTest(httpPort = 8001)
class AgentServiceClientTest {
    
    @Autowired
    private AgentServiceClient agentServiceClient;
    
    @Test
    void shouldGenerateWorkoutPlan() {
        // Arrange
        stubFor(post("/api/v1/plans/generate")
            .willReturn(aResponse()
                .withStatus(202)
                .withHeader("Content-Type", "application/json")
                .withBody("{\"requestId\":\"req-001\",\"status\":\"processing\"}")));
        
        // Act
        PlanResponse response = agentServiceClient.generatePlan(request);
        
        // Assert
        assertThat(response.getRequestId()).isEqualTo("req-001");
        verify(postRequestedFor(urlEqualTo("/api/v1/plans/generate")));
    }
}
```

---

## Performance Tests

### Load Testing with JMeter

Test plan located at: `src/test/jmeter/load-test.jmx`

**Scenarios:**
1. User registration and login (100 users/sec)
2. Workout session creation (50 sessions/sec)
3. Real-time posture feedback (20 concurrent streams)

**Thresholds:**
- P95 latency < 500ms
- Error rate < 0.1%
- Throughput > 1000 req/sec

```bash
# Run load test
jmeter -n -t src/test/jmeter/load-test.jmx -l results.jtl

# Generate HTML report
jmeter -g results.jtl -o report/
```

---

## Test Data Management

### Test Fixtures

Use builder pattern for test data:

```java
public class UserTestDataBuilder {
    
    public static User.UserBuilder aUser() {
        return User.builder()
            .id(UUID.randomUUID())
            .email("test@example.com")
            .password("$2a$10$...")
            .name("Test User")
            .age(30)
            .gender("male")
            .fitnessLevel("intermediate")
            .createdAt(Instant.now())
            .updatedAt(Instant.now());
    }
    
    public static User.UserBuilder anAdvancedUser() {
        return aUser()
            .fitnessLevel("advanced")
            .age(25);
    }
}
```

### Database Cleanup

Use `@Transactional` and `@Rollback` for automatic cleanup:

```java
@SpringBootTest
@Transactional
class MyIntegrationTest {
    // Tests automatically rolled back after execution
}
```

Or manual cleanup in `@AfterEach`:

```java
@AfterEach
void cleanup() {
    userRepository.deleteAll();
    workoutRepository.deleteAll();
}
```

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on every PR:

```yaml
# .github/workflows/backend-api-ci.yml
- name: Run unit tests
  run: ./gradlew test

- name: Run integration tests
  run: ./gradlew integrationTest

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./build/reports/jacoco/test/jacocoTestReport.xml
```

### Quality Gates

PR cannot be merged if:
- [ ] Any test fails
- [ ] Coverage drops below 80%
- [ ] Critical security vulnerabilities found
- [ ] Code style violations

---

## Troubleshooting

### TestContainers Issues

**Problem:** TestContainers timeout

**Solution:**
```bash
# Check Docker is running
docker ps

# Pull images manually
docker pull postgres:16-alpine
docker pull redis:7-alpine
```

### Flaky Tests

**Problem:** Tests pass/fail randomly

**Common Causes:**
1. Timing issues - Use awaitility
2. Shared state - Ensure proper cleanup
3. External dependencies - Use mocks

**Solution:**
```java
// Use Awaitility for async operations
await()
    .atMost(5, SECONDS)
    .until(() -> userRepository.findByEmail("test@example.com").isPresent());
```

### Out of Memory

**Problem:** Tests fail with OOM

**Solution:**
```bash
# Increase heap size
export GRADLE_OPTS="-Xmx2048m -XX:MaxMetaspaceSize=512m"
./gradlew test
```

---

## Best Practices

1. **Test Names:** Use descriptive names with `@DisplayName`
2. **AAA Pattern:** Arrange, Act, Assert
3. **One Assertion:** Focus on one behavior per test
4. **Mock Sparingly:** Prefer real objects when possible
5. **Fast Tests:** Unit tests should run in milliseconds
6. **Isolated Tests:** No dependencies between tests
7. **Test Coverage:** Cover happy path, edge cases, and error cases

---

**Last Updated:** 2026-05-18  
**Maintained By:** Backend Team
