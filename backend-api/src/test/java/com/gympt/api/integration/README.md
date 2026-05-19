# Integration Tests

This directory contains integration tests that test multiple components together.

## Structure

```
integration/
├── api/             # API endpoint tests
├── database/        # Database integration tests
└── external/        # External service integration tests
```

## TestContainers

Integration tests use TestContainers to spin up real PostgreSQL and Redis instances.

## Running Tests

```bash
# All integration tests
./gradlew integrationTest

# Specific test
./gradlew integrationTest --tests UserControllerIntegrationTest
```
