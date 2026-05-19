# Backend API - Environment Variables

## Overview

This document lists all environment variables used by the backend-api service across different environments (local, dev, prod).

## Configuration Profiles

| Profile | Purpose | Config Source |
|---------|---------|---------------|
| `local` | Local development | `.env` file |
| `dev` | AWS dev environment | AWS Secrets Manager + SSM Parameter Store |
| `prod` | Production | AWS Secrets Manager + SSM Parameter Store |

---

## Environment Variables

### Application Configuration

#### APP_ENV
- **Description:** Application environment identifier
- **Type:** String
- **Required:** Yes
- **Default:** `local`
- **Valid Values:** `local`, `dev`, `prod`
- **Example:** `APP_ENV=local`

#### SPRING_PROFILES_ACTIVE
- **Description:** Spring Boot active profile
- **Type:** String
- **Required:** Yes
- **Default:** `local`
- **Valid Values:** `local`, `dev`, `prod`
- **Example:** `SPRING_PROFILES_ACTIVE=local`

#### SERVICE_NAME
- **Description:** Service identifier for logging and monitoring
- **Type:** String
- **Required:** Yes
- **Default:** `backend-api`
- **Example:** `SERVICE_NAME=backend-api`

#### LOG_LEVEL
- **Description:** Application logging level
- **Type:** String
- **Required:** No
- **Default:** `INFO`
- **Valid Values:** `DEBUG`, `INFO`, `WARN`, `ERROR`
- **Example:** `LOG_LEVEL=DEBUG`

---

### Database Configuration

#### DB_HOST
- **Description:** PostgreSQL database hostname
- **Type:** String
- **Required:** Yes
- **Local:** `localhost` or `postgres` (docker)
- **Dev/Prod:** RDS endpoint
- **Example:** `DB_HOST=localhost`

#### DB_PORT
- **Description:** PostgreSQL database port
- **Type:** Integer
- **Required:** Yes
- **Default:** `5432`
- **Example:** `DB_PORT=5432`

#### DB_NAME
- **Description:** Database name
- **Type:** String
- **Required:** Yes
- **Default:** `gympt`
- **Example:** `DB_NAME=gympt`

#### DB_USERNAME
- **Description:** Database username
- **Type:** String
- **Required:** Yes
- **Local:** `gympt_user`
- **Dev/Prod:** From AWS Secrets Manager
- **Example:** `DB_USERNAME=gympt_user`

#### DB_PASSWORD
- **Description:** Database password
- **Type:** String (Sensitive)
- **Required:** Yes
- **Local:** `gympt_local_pass`
- **Dev/Prod:** From AWS Secrets Manager (`/gympt/{env}/rds/password`)
- **Example:** `DB_PASSWORD=changeme_local_password`

#### DB_POOL_SIZE
- **Description:** Database connection pool maximum size
- **Type:** Integer
- **Required:** No
- **Default:** `10`
- **Prod Recommended:** `20`
- **Example:** `DB_POOL_SIZE=10`

---

### Cache Configuration (Redis)

#### REDIS_HOST
- **Description:** Redis server hostname
- **Type:** String
- **Required:** Yes
- **Local:** `localhost` or `redis` (docker)
- **Dev/Prod:** ElastiCache endpoint
- **Example:** `REDIS_HOST=localhost`

#### REDIS_PORT
- **Description:** Redis server port
- **Type:** Integer
- **Required:** Yes
- **Default:** `6379`
- **Example:** `REDIS_PORT=6379`

#### REDIS_PASSWORD
- **Description:** Redis authentication password
- **Type:** String (Sensitive)
- **Required:** No (local), Yes (dev/prod)
- **Local:** Empty
- **Dev/Prod:** From AWS Secrets Manager (`/gympt/{env}/redis/auth-token`)
- **Example:** `REDIS_PASSWORD=`

#### REDIS_TTL
- **Description:** Default cache TTL in seconds
- **Type:** Integer
- **Required:** No
- **Default:** `3600`
- **Example:** `REDIS_TTL=3600`

---

### AWS Configuration

#### AWS_REGION
- **Description:** AWS region for all services
- **Type:** String
- **Required:** Yes
- **Default:** `ap-northeast-2`
- **Example:** `AWS_REGION=ap-northeast-2`

#### AWS_ACCESS_KEY_ID
- **Description:** AWS access key (local only)
- **Type:** String
- **Required:** Local only
- **Local:** `test` (for LocalStack)
- **Dev/Prod:** Use IRSA (IAM Roles for Service Accounts)
- **Example:** `AWS_ACCESS_KEY_ID=test`

#### AWS_SECRET_ACCESS_KEY
- **Description:** AWS secret key (local only)
- **Type:** String (Sensitive)
- **Required:** Local only
- **Local:** `test` (for LocalStack)
- **Dev/Prod:** Use IRSA
- **Example:** `AWS_SECRET_ACCESS_KEY=test`

---

### S3 Configuration

#### S3_ENDPOINT_URL
- **Description:** S3 endpoint URL (local only)
- **Type:** String
- **Required:** Local only
- **Local:** `http://localhost:4566`
- **Dev/Prod:** Not set (use default AWS endpoint)
- **Example:** `S3_ENDPOINT_URL=http://localhost:4566`

#### S3_MEDIA_BUCKET
- **Description:** S3 bucket for user media (profile images, workout videos)
- **Type:** String
- **Required:** Yes
- **Local:** `gympt-media-local`
- **Dev:** From Parameter Store (`/gympt/dev/s3/media-bucket`)
- **Prod:** From Parameter Store (`/gympt/prod/s3/media-bucket`)
- **Example:** `S3_MEDIA_BUCKET=gympt-media-local`

#### S3_REPORT_BUCKET
- **Description:** S3 bucket for generated reports
- **Type:** String
- **Required:** Yes
- **Local:** `gympt-reports-local`
- **Dev/Prod:** From Parameter Store
- **Example:** `S3_REPORT_BUCKET=gympt-reports-local`

---

### SQS Configuration

#### SQS_ENDPOINT_URL
- **Description:** SQS endpoint URL (local only)
- **Type:** String
- **Required:** Local only
- **Local:** `http://localhost:4566`
- **Example:** `SQS_ENDPOINT_URL=http://localhost:4566`

#### SQS_POSTURE_EVENT_QUEUE_URL
- **Description:** Queue for posture analysis events
- **Type:** String
- **Required:** Yes
- **Local:** `http://localhost:4566/000000000000/gympt-posture-events-local`
- **Dev/Prod:** From Parameter Store
- **Example:** `SQS_POSTURE_EVENT_QUEUE_URL=http://localhost:4566/000000000000/gympt-posture-events-local`

#### SQS_REPORT_GENERATION_QUEUE_URL
- **Description:** Queue for report generation tasks
- **Type:** String
- **Required:** Yes
- **Example:** `SQS_REPORT_GENERATION_QUEUE_URL=http://localhost:4566/000000000000/gympt-report-generation-local`

---

### DynamoDB Configuration

#### DYNAMODB_ENDPOINT_URL
- **Description:** DynamoDB endpoint URL (local only)
- **Type:** String
- **Required:** Local only
- **Local:** `http://localhost:8000`
- **Example:** `DYNAMODB_ENDPOINT_URL=http://localhost:8000`

#### DYNAMODB_WORKOUT_SESSIONS_TABLE
- **Description:** DynamoDB table for workout session events
- **Type:** String
- **Required:** Yes
- **Local:** `gympt-workout-sessions-local`
- **Dev/Prod:** From Parameter Store
- **Example:** `DYNAMODB_WORKOUT_SESSIONS_TABLE=gympt-workout-sessions-local`

#### DYNAMODB_POSTURE_EVENTS_TABLE
- **Description:** DynamoDB table for posture analysis events
- **Type:** String
- **Required:** Yes
- **Example:** `DYNAMODB_POSTURE_EVENTS_TABLE=gympt-posture-events-local`

---

### EventBridge Configuration

#### EVENTBRIDGE_ENDPOINT_URL
- **Description:** EventBridge endpoint URL (local only)
- **Type:** String
- **Required:** Local only
- **Local:** `http://localhost:4566`
- **Example:** `EVENTBRIDGE_ENDPOINT_URL=http://localhost:4566`

#### EVENTBRIDGE_BUS_NAME
- **Description:** Event bus for domain events
- **Type:** String
- **Required:** Yes
- **Local:** `gympt-events-local`
- **Dev/Prod:** From Parameter Store
- **Example:** `EVENTBRIDGE_BUS_NAME=gympt-events-local`

---

### Microservices Integration

#### AGENT_SERVICE_BASE_URL
- **Description:** Base URL for agent-service
- **Type:** String
- **Required:** Yes
- **Local:** `http://localhost:8001` or `http://agent-service:8001` (docker)
- **Dev/Prod:** Kubernetes service DNS
- **Example:** `AGENT_SERVICE_BASE_URL=http://agent-service:8001`

#### POSTURE_ANALYSIS_SERVICE_BASE_URL
- **Description:** Base URL for posture-analysis-service
- **Type:** String
- **Required:** Yes
- **Local:** `http://localhost:8002`
- **Example:** `POSTURE_ANALYSIS_SERVICE_BASE_URL=http://posture-analysis-service:8002`

#### REPORT_SERVICE_BASE_URL
- **Description:** Base URL for report-service
- **Type:** String
- **Required:** Yes
- **Example:** `REPORT_SERVICE_BASE_URL=http://report-service:8003`

#### NOTIFICATION_SERVICE_BASE_URL
- **Description:** Base URL for notification-service
- **Type:** String
- **Required:** Yes
- **Example:** `NOTIFICATION_SERVICE_BASE_URL=http://notification-service:8004`

---

### Security Configuration

#### JWT_SECRET
- **Description:** Secret key for JWT token signing
- **Type:** String (Sensitive)
- **Required:** Yes
- **Local:** `local_jwt_secret_for_development_only`
- **Dev/Prod:** From AWS Secrets Manager (`/gympt/{env}/jwt/secret`)
- **Security:** Must be strong random string, minimum 256 bits
- **Example:** `JWT_SECRET=local_jwt_secret_for_development_only`

#### JWT_EXPIRATION
- **Description:** JWT access token expiration in seconds
- **Type:** Integer
- **Required:** No
- **Default:** `3600` (1 hour)
- **Example:** `JWT_EXPIRATION=3600`

#### JWT_REFRESH_EXPIRATION
- **Description:** JWT refresh token expiration in seconds
- **Type:** Integer
- **Required:** No
- **Default:** `604800` (7 days)
- **Example:** `JWT_REFRESH_EXPIRATION=604800`

---

### API Configuration

#### CORS_ORIGINS
- **Description:** Allowed CORS origins (comma-separated)
- **Type:** String
- **Required:** Yes
- **Local:** `http://localhost:3000,http://localhost:3001`
- **Dev:** `https://dev.gympt.example.com`
- **Prod:** `https://gympt.example.com`
- **Example:** `CORS_ORIGINS=http://localhost:3000,http://localhost:3001`

#### ENABLE_API_DOCS
- **Description:** Enable Swagger/OpenAPI documentation
- **Type:** Boolean
- **Required:** No
- **Default:** `true` (local/dev), `false` (prod)
- **Example:** `ENABLE_API_DOCS=true`

#### API_RATE_LIMIT_PER_HOUR
- **Description:** API rate limit per user per hour
- **Type:** Integer
- **Required:** No
- **Default:** `1000`
- **Example:** `API_RATE_LIMIT_PER_HOUR=1000`

---

## Environment-Specific Configuration

### Local Development

```bash
# Application
APP_ENV=local
SPRING_PROFILES_ACTIVE=local
LOG_LEVEL=DEBUG

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gympt
DB_USERNAME=gympt_user
DB_PASSWORD=gympt_local_pass

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# AWS (LocalStack)
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localhost:4566
SQS_ENDPOINT_URL=http://localhost:4566
DYNAMODB_ENDPOINT_URL=http://localhost:8000
EVENTBRIDGE_ENDPOINT_URL=http://localhost:4566

# Services
AGENT_SERVICE_BASE_URL=http://localhost:8001
POSTURE_ANALYSIS_SERVICE_BASE_URL=http://localhost:8002

# Security
JWT_SECRET=local_jwt_secret_for_development_only
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ENABLE_API_DOCS=true
```

### AWS Dev Environment

Most configuration comes from:
- **Secrets Manager:** `/gympt/dev/*` (passwords, API keys)
- **Parameter Store:** `/gympt/dev/*` (non-sensitive config)
- **Kubernetes ConfigMap:** `backend-api-config`
- **Kubernetes Secret:** `backend-api-secrets` (from External Secrets Operator)

### AWS Prod Environment

Same as dev but with:
- Stricter rate limits
- API docs disabled
- Enhanced monitoring
- Multi-AZ resources

---

## Validation

### Required Variables Check

The application validates required variables on startup:

```java
@ConfigurationProperties(prefix = "app")
@Validated
public class AppConfig {
    @NotNull
    private String env;
    
    @NotNull
    private String jwtSecret;
    
    // ... other validations
}
```

### Startup Failure

If required variables are missing, the application will:
1. Log clear error message indicating which variables are missing
2. Exit with non-zero status code
3. Kubernetes will restart the pod (readiness probe will fail)

---

## Security Best Practices

1. **Never commit secrets to Git**
   - Use `.env` for local (excluded by `.gitignore`)
   - Use AWS Secrets Manager for dev/prod

2. **Rotate credentials regularly**
   - JWT secret: Every 90 days
   - Database passwords: Every 180 days
   - API keys: As needed

3. **Use least privilege**
   - Service account IAM roles should have minimal permissions
   - Database user should only access necessary tables

4. **Audit access**
   - Log all Secrets Manager access
   - Alert on unexpected secret retrievals

---

## Troubleshooting

### Missing Environment Variable

**Error:**
```
Binding validation errors:
  - Field error in object 'appConfig' on field 'jwtSecret': rejected value [null]
```

**Solution:**
1. Check if variable is set: `echo $JWT_SECRET`
2. For local: Verify `.env` file exists and is loaded
3. For Kubernetes: Check ConfigMap and Secret are created

### Wrong Endpoint URL

**Error:**
```
Unable to execute HTTP request: Connection refused
```

**Solution:**
1. Verify service is running: `docker ps` or `kubectl get pods`
2. Check endpoint URL format (include protocol: `http://`)
3. For LocalStack: Ensure container is healthy

---

**Last Updated:** 2026-05-18  
**Maintained By:** Backend Team
