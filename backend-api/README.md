# Backend API Service

## Overview

**Technology:** Spring Boot 3.2, Java 17, PostgreSQL, Redis  
**Port:** 8080  
**Purpose:** Main REST API for GYMPT platform, handling user management, workout plans, subscriptions, and orchestrating calls to other microservices.

### Key Features
- User authentication and authorization (JWT)
- User profile and body metrics management
- Workout session management
- Integration with AI Agent service
- Integration with Posture Analysis service
- Video streaming coordination (Kinesis Video Streams)
- Report generation orchestration
- Exercise library management
- Subscription and payment processing

### Dependencies
- **Database:** PostgreSQL (user data, workout plans, subscriptions)
- **Cache:** Redis (session cache, API rate limiting)
- **External Services:**
  - agent-service (AI recommendations)
  - posture-analysis-service (posture analysis)
  - notification-service (alerts and notifications)
- **AWS Services:**
  - S3 (profile images, workout media)
  - SQS (async task queue)
  - EventBridge (domain events)
  - Kinesis Video Streams (live video)

---

## Development Process Checklist

Follow the [Service Development Process](../docs/service-development-process.md) for this service.

### Phase 1: Design & Specification

- [ ] **1. Requirements Definition** - Completed in this README
- [ ] **2. API Specification** - See [docs/api.md](./docs/api.md)
- [ ] **3. Data Model Definition** - See schema section below
- [ ] **4. Environment Variables** - See [docs/env.md](./docs/env.md)

### Phase 2: Implementation

- [ ] **5. Local Execution Setup** - Instructions in Quick Start section
- [ ] **6. Unit Tests** - See `src/test/java/com/gympt/api/unit/`
- [ ] **7. Integration Tests** - See `src/test/java/com/gympt/api/integration/`

### Phase 3: Containerization

- [ ] **8. Dockerfile** - See `Dockerfile`
- [ ] **9. Local Docker Compose Validation** - Test with `../local/docker-compose.yml`

### Phase 4: CI/CD

- [ ] **10. GitHub Actions CI** - See `../.github/workflows/backend-api-ci.yml`
- [ ] **11. Helm Chart Values** - See `../../gympt-gitops/apps/backend-api/values-dev.yaml`
- [ ] **12. AWS Dev Deployment** - Deploy via Argo CD

### Phase 5: Observability

- [ ] **13. Monitoring Metrics** - Prometheus metrics at `/actuator/prometheus`
- [ ] **14. Logging and Alerting** - Structured JSON logs to CloudWatch

### Phase 6: Production Readiness

- [ ] **15. Production Considerations** - See [docs/deploy.md](./docs/deploy.md#production)

---

## 🛠️ Tech Stack

- **Framework**: Spring Boot 3.2
- **Language**: Java 17
- **Security**: Spring Security + JWT
- **Database**: Spring Data JPA + PostgreSQL
- **Cache**: Spring Data Redis
- **AWS**: Spring Cloud AWS
- **Build**: Gradle 8.7
- **Testing**: JUnit 5, Testcontainers

## 🚀 Quick Start

### Prerequisites

- JDK 17+
- Gradle 8.7+
- PostgreSQL 16+
- Redis 7+

### Local Development

```bash
# 1. Set environment variables
cp ../.env.example ../.env
# Edit .env file

# 2. Start dependencies
cd ../local
./scripts/start-local-infra.sh

# 3. Run application
./gradlew bootRun --args='--spring.profiles.active=local'
```

Application will start at http://localhost:8080

### API Documentation

Swagger UI: http://localhost:8080/swagger-ui.html

## 📁 Project Structure

```
backend-api/
├── src/
│   ├── main/
│   │   ├── java/com/gympt/api/
│   │   │   ├── config/          # Configuration classes
│   │   │   ├── controller/      # REST controllers
│   │   │   ├── service/         # Business logic
│   │   │   ├── repository/      # Data access layer
│   │   │   ├── domain/          # JPA entities
│   │   │   ├── dto/             # Data transfer objects
│   │   │   └── exception/       # Custom exceptions
│   │   └── resources/
│   │       ├── application.yml  # Application config
│   │       └── db/migration/    # Flyway migrations
│   └── test/
│       └── java/com/gympt/api/
│           ├── controller/      # Controller tests
│           ├── service/         # Service tests
│           └── integration/     # Integration tests
├── build.gradle                 # Gradle build file
└── Dockerfile                   # Docker image
```

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/{id}` - Get user by ID

### Workouts
- `GET /api/v1/workouts` - List workouts
- `POST /api/v1/workouts` - Create workout session
- `GET /api/v1/workouts/{id}` - Get workout details
- `PUT /api/v1/workouts/{id}` - Update workout
- `DELETE /api/v1/workouts/{id}` - Delete workout

### AI Agent
- `POST /api/v1/agent/plan` - Generate workout plan
- `POST /api/v1/agent/advice` - Get nutrition advice
- `POST /api/v1/agent/chat` - Chat with AI agent

### Video Streaming
- `POST /api/v1/streams/start` - Start video stream
- `POST /api/v1/streams/stop` - Stop video stream
- `GET /api/v1/streams/{id}` - Get stream details

### Reports
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/{id}` - Get report details
- `POST /api/v1/reports/{id}/download` - Download report PDF

## 🧪 Testing

### Unit Tests

```bash
./gradlew test
```

### Integration Tests

```bash
./gradlew integrationTest
```

### Test Coverage

```bash
./gradlew jacocoTestReport
open build/reports/jacoco/test/html/index.html
```

## 🔒 Security

### Authentication Flow

1. User sends credentials to `/auth/login`
2. Server validates credentials
3. Server generates JWT token
4. Client includes JWT in `Authorization: Bearer <token>` header
5. Server validates JWT on protected endpoints

### JWT Configuration

- **Algorithm**: HS256
- **Expiration**: 1 hour (configurable)
- **Refresh Token**: 7 days (configurable)
- **Secret**: Stored in AWS Secrets Manager (production)

### Password Hashing

- **Algorithm**: BCrypt
- **Strength**: 10 rounds

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER,
    gender VARCHAR(10),
    fitness_level VARCHAR(20),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Workouts Table
```sql
CREATE TABLE workouts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    duration INTEGER NOT NULL,
    calories INTEGER,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🐳 Docker

### Build Image

```bash
docker build -t gympt/backend-api:latest .
```

### Run Container

```bash
docker run -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=local \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  gympt/backend-api:latest
```

## 📈 Monitoring

### Health Check

```bash
curl http://localhost:8080/actuator/health
```

### Metrics (Prometheus)

```bash
curl http://localhost:8080/actuator/prometheus
```

### Available Metrics

- JVM memory usage
- HTTP request duration
- Database connection pool
- Redis cache hit/miss ratio
- Custom business metrics

## 🔧 Configuration

### Environment Variables

See `../.env.example` for all available environment variables.

### Application Profiles

- `local`: Local development
- `dev`: Development environment (AWS)
- `prod`: Production environment (AWS)

## 🚀 Deployment

Deployment is managed via GitOps (Argo CD).

1. Code is pushed to `main` branch
2. GitHub Actions builds Docker image
3. Image is pushed to ECR
4. GitOps repository is updated
5. Argo CD syncs and deploys to EKS

## 📚 Additional Documentation

- [API Specifications](../docs/api/backend-api.md)
- [Database Migrations](../docs/database/migrations.md)
- [Security Best Practices](../docs/security/backend-api.md)

## 🤝 Contributing

1. Create feature branch
2. Write tests for new features
3. Ensure all tests pass
4. Create Pull Request

## 📝 License

Proprietary - All rights reserved
