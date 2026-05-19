# Backend API Specification

## Base URL

- **Local:** `http://localhost:8080`
- **Dev:** `https://api.dev.gympt.example.com`
- **Prod:** `https://api.gympt.example.com`

## API Version

Current version: `v1`

All endpoints are prefixed with `/api/v1`

---

## Authentication

### Authentication Flow

1. User registers or logs in
2. Server returns JWT access token and refresh token
3. Client includes access token in `Authorization` header for all protected endpoints
4. When access token expires, use refresh token to get new access token

### Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Endpoints

### Authentication

#### POST /api/v1/auth/register

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "name": "John Doe",
  "age": 30,
  "gender": "male",
  "fitnessLevel": "intermediate"
}
```

**Response:** `201 Created`
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "accessToken": "eyJhbGc...",
  "refreshToken": "eyJhbGc...",
  "expiresIn": 3600
}
```

**Errors:**
- `400` - Validation error (weak password, invalid email)
- `409` - Email already exists

---

#### POST /api/v1/auth/login

Authenticate existing user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```

**Response:** `200 OK`
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "accessToken": "eyJhbGc...",
  "refreshToken": "eyJhbGc...",
  "expiresIn": 3600
}
```

**Errors:**
- `401` - Invalid credentials

---

#### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refreshToken": "eyJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "accessToken": "eyJhbGc...",
  "expiresIn": 3600
}
```

**Errors:**
- `401` - Invalid or expired refresh token

---

#### POST /api/v1/auth/logout

Logout user and invalidate tokens.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `204 No Content`

---

### Users

#### GET /api/v1/users/me

Get current user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "age": 30,
  "gender": "male",
  "fitnessLevel": "intermediate",
  "bodyProfile": {
    "height": 175,
    "weight": 75,
    "bodyFat": 18.5,
    "muscleMass": 35.2
  },
  "subscriptionStatus": "active",
  "createdAt": "2026-05-01T10:00:00Z",
  "updatedAt": "2026-05-18T15:30:00Z"
}
```

---

#### PUT /api/v1/users/me

Update current user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "name": "John Doe Updated",
  "age": 31,
  "bodyProfile": {
    "height": 175,
    "weight": 73,
    "bodyFat": 17.0,
    "muscleMass": 36.5
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe Updated",
  "age": 31,
  "bodyProfile": {
    "height": 175,
    "weight": 73,
    "bodyFat": 17.0,
    "muscleMass": 36.5
  },
  "updatedAt": "2026-05-18T16:00:00Z"
}
```

---

### Workout Plans

#### GET /api/v1/workout-plans

List user's workout plans.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `page` (int, default: 0)
- `size` (int, default: 20)
- `status` (string: "active", "completed", "draft")

**Response:** `200 OK`
```json
{
  "content": [
    {
      "id": "plan-001",
      "name": "8-Week Strength Building",
      "goal": "muscle_gain",
      "duration": 8,
      "status": "active",
      "createdAt": "2026-05-01T10:00:00Z",
      "startDate": "2026-05-01",
      "endDate": "2026-06-26"
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 1,
  "totalPages": 1
}
```

---

#### POST /api/v1/workout-plans

Create new workout plan.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "name": "Custom Strength Plan",
  "goal": "muscle_gain",
  "duration": 12,
  "startDate": "2026-05-20",
  "exercises": [
    {
      "exerciseId": "ex-squat-001",
      "sets": 4,
      "reps": 8,
      "restSeconds": 90,
      "dayOfWeek": 1
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "plan-002",
  "name": "Custom Strength Plan",
  "goal": "muscle_gain",
  "duration": 12,
  "status": "draft",
  "createdAt": "2026-05-18T16:30:00Z"
}
```

---

### Workout Sessions

#### POST /api/v1/workout-sessions

Start a new workout session.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "workoutPlanId": "plan-001",
  "plannedDuration": 3600,
  "exercises": ["ex-squat-001", "ex-bench-001"]
}
```

**Response:** `201 Created`
```json
{
  "sessionId": "session-001",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "workoutPlanId": "plan-001",
  "status": "in_progress",
  "startTime": "2026-05-18T16:45:00Z",
  "streamingUrl": "wss://stream.gympt.example.com/session-001"
}
```

---

#### PUT /api/v1/workout-sessions/{sessionId}/complete

Complete a workout session.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "actualDuration": 3420,
  "caloriesBurned": 450,
  "notes": "Great session, felt strong on squats"
}
```

**Response:** `200 OK`
```json
{
  "sessionId": "session-001",
  "status": "completed",
  "startTime": "2026-05-18T16:45:00Z",
  "endTime": "2026-05-18T17:42:00Z",
  "duration": 3420,
  "caloriesBurned": 450,
  "postureScore": 8.5,
  "formIssues": 3
}
```

---

### AI Agent Integration

#### POST /api/v1/agent/generate-plan

Generate AI-powered workout plan.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "goal": "muscle_gain",
  "experience": "intermediate",
  "daysPerWeek": 4,
  "equipmentAvailable": ["barbell", "dumbbell", "bench"],
  "duration": 8
}
```

**Response:** `202 Accepted`
```json
{
  "requestId": "req-001",
  "status": "processing",
  "estimatedCompletion": "2026-05-18T16:50:00Z"
}
```

**Async Result:** Event sent to client via WebSocket or retrieved via polling

---

#### POST /api/v1/agent/chat

Chat with AI trainer.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "message": "How can I improve my squat form?",
  "sessionId": "chat-session-001",
  "context": {
    "recentWorkouts": ["session-001"],
    "currentGoal": "muscle_gain"
  }
}
```

**Response:** `200 OK`
```json
{
  "message": "To improve your squat form, focus on these key points: 1) Keep your chest up...",
  "sessionId": "chat-session-001",
  "suggestions": [
    {
      "type": "exercise",
      "id": "ex-goblet-squat-001",
      "reason": "Great for learning proper depth and balance"
    }
  ]
}
```

---

### Reports

#### GET /api/v1/reports

List available reports.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `page` (int)
- `size` (int)
- `type` (string: "weekly", "monthly", "progress")

**Response:** `200 OK`
```json
{
  "content": [
    {
      "id": "report-001",
      "type": "weekly",
      "period": "2026-05-12 to 2026-05-18",
      "status": "ready",
      "generatedAt": "2026-05-18T23:00:00Z",
      "downloadUrl": "https://s3.amazonaws.com/gympt-reports/report-001.pdf"
    }
  ],
  "page": 0,
  "totalElements": 5
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "timestamp": "2026-05-18T17:00:00Z",
    "path": "/api/v1/auth/register"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate email) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependent service unavailable |

---

## Rate Limiting

- **Anonymous requests:** 100 requests/hour per IP
- **Authenticated requests:** 1000 requests/hour per user
- **Streaming endpoints:** 10 concurrent sessions per user

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1621363200
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page` - Page number (0-indexed)
- `size` - Items per page (max 100)
- `sort` - Sort field and direction (e.g., `createdAt,desc`)

**Response Format:**
```json
{
  "content": [...],
  "page": 0,
  "size": 20,
  "totalElements": 150,
  "totalPages": 8,
  "first": true,
  "last": false
}
```

---

## WebSocket Endpoints

### /ws/workout-sessions/{sessionId}

Real-time workout session updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://api.gympt.example.com/ws/workout-sessions/session-001?token=<access_token>');
```

**Messages:**
```json
{
  "type": "posture_feedback",
  "data": {
    "exerciseId": "ex-squat-001",
    "score": 8.5,
    "issues": ["knee_valgus"],
    "timestamp": "2026-05-18T17:00:00Z"
  }
}
```

---

## OpenAPI Specification

Download full OpenAPI 3.0 spec:
- **Local:** http://localhost:8080/v3/api-docs
- **Dev:** https://api.dev.gympt.example.com/v3/api-docs

Interactive documentation:
- **Local:** http://localhost:8080/swagger-ui.html
- **Dev:** https://api.dev.gympt.example.com/swagger-ui.html

---

**Last Updated:** 2026-05-18  
**API Version:** v1.0.0
