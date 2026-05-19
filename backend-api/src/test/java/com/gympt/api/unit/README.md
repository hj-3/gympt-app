# Unit Tests

This directory contains unit tests for individual components.

## Structure

```
unit/
├── controller/      # Controller layer tests
├── service/         # Business logic tests
├── repository/      # Repository tests (with H2)
├── security/        # Security component tests
└── utils/           # Utility class tests
```

## Example Test

See `UserServiceTest.java` for a complete example of service unit testing with Mockito.

## Running Tests

```bash
# All unit tests
./gradlew test

# Specific test
./gradlew test --tests UserServiceTest
```
