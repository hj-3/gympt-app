# GYMPT API 문서

> GYMPT 플랫폼의 RESTful API 및 WebSocket API 레퍼런스

## 목차

1. [인증](#인증)
2. [Backend API](#backend-api)
3. [Agent Service API](#agent-service-api)
4. [Posture Analysis API](#posture-analysis-api)
5. [에러 처리](#에러-처리)
6. [Rate Limiting](#rate-limiting)

---

## 인증

### JWT 인증 방식

모든 보호된 엔드포인트는 JWT Bearer Token을 요구합니다.

**헤더:**
```http
Authorization: Bearer <access_token>
```

### 로그인

**POST** `/api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Password1!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "refresh_token_here",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### 토큰 갱신

**POST** `/api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response (200 OK):**
```json
{
  "access_token": "new_access_token",
  "expires_in": 900
}
```

---

## Backend API

Base URL: `https://api.gympt.com` (prod) / `http://localhost:8080` (local)

### 사용자 관리

#### 회원가입

**POST** `/api/v1/auth/signup`

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "Password1!",
  "name": "홍길동",
  "phone": "010-1234-5678"
}
```

**Response (201 Created):**
```json
{
  "user_id": 123,
  "email": "newuser@example.com",
  "name": "홍길동",
  "created_at": "2026-05-19T12:00:00Z"
}
```

#### 내 정보 조회

**GET** `/api/v1/users/me`

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "name": "홍길동",
  "phone": "010-1234-5678",
  "fitness_level": "intermediate",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-05-19T12:00:00Z"
}
```

---

### 운동 계획 (Workouts)

#### 운동 계획 목록 조회

**GET** `/api/v1/workouts`

**Query Parameters:**
- `page`: 페이지 번호 (default: 0)
- `size`: 페이지 크기 (default: 20, max: 100)
- `status`: 필터 (active, completed, all)

**Response (200 OK):**
```json
{
  "content": [
    {
      "workout_id": 456,
      "title": "상체 집중 운동",
      "description": "가슴, 어깨, 삼두근 중심",
      "exercises": [
        {
          "exercise_id": 1,
          "name": "벤치프레스",
          "sets": 3,
          "reps": 10,
          "weight_kg": 60
        }
      ],
      "status": "active",
      "created_at": "2026-05-18T10:00:00Z"
    }
  ],
  "page": {
    "size": 20,
    "number": 0,
    "total_elements": 50,
    "total_pages": 3
  }
}
```

#### 운동 계획 생성

**POST** `/api/v1/workouts`

**Request:**
```json
{
  "title": "하체 운동",
  "description": "스쿼트, 런지 중심",
  "exercises": [
    {
      "exercise_name": "스쿼트",
      "sets": 3,
      "reps": 15,
      "weight_kg": 80
    },
    {
      "exercise_name": "런지",
      "sets": 3,
      "reps": 12,
      "weight_kg": 0
    }
  ],
  "target_date": "2026-05-20"
}
```

**Response (201 Created):**
```json
{
  "workout_id": 789,
  "title": "하체 운동",
  "exercises": [...],
  "status": "active",
  "created_at": "2026-05-19T12:00:00Z"
}
```

---

### 운동 세션 (Sessions)

#### 세션 시작

**POST** `/api/v1/sessions`

**Request:**
```json
{
  "workout_id": 456,
  "stream_name": "kvs-stream-123"
}
```

**Response (201 Created):**
```json
{
  "session_id": "sess_abc123",
  "workout_id": 456,
  "status": "in_progress",
  "started_at": "2026-05-19T12:00:00Z",
  "kvs_stream_name": "kvs-stream-123",
  "websocket_url": "wss://api.gympt.com/ws/session/sess_abc123"
}
```

#### 세션 종료

**PUT** `/api/v1/sessions/{session_id}/complete`

**Response (200 OK):**
```json
{
  "session_id": "sess_abc123",
  "status": "completed",
  "started_at": "2026-05-19T12:00:00Z",
  "ended_at": "2026-05-19T12:45:00Z",
  "duration_seconds": 2700,
  "exercises_completed": 5
}
```

---

### 인바디 데이터 (Body Profiles)

#### 인바디 데이터 등록

**POST** `/api/v1/body-profiles`

**Request:**
```json
{
  "measurement_date": "2026-05-19",
  "weight_kg": 75.5,
  "height_cm": 175,
  "body_fat_percentage": 18.5,
  "muscle_mass_kg": 32.5,
  "bmr": 1650
}
```

**Response (201 Created):**
```json
{
  "profile_id": 101,
  "user_id": 123,
  "measurement_date": "2026-05-19",
  "weight_kg": 75.5,
  "bmi": 24.7,
  "body_fat_percentage": 18.5,
  "created_at": "2026-05-19T12:00:00Z"
}
```

#### 인바디 이력 조회

**GET** `/api/v1/body-profiles`

**Query Parameters:**
- `from`: 시작일 (YYYY-MM-DD)
- `to`: 종료일 (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "profiles": [
    {
      "profile_id": 101,
      "measurement_date": "2026-05-19",
      "weight_kg": 75.5,
      "body_fat_percentage": 18.5
    },
    {
      "profile_id": 100,
      "measurement_date": "2026-05-01",
      "weight_kg": 76.2,
      "body_fat_percentage": 19.0
    }
  ]
}
```

---

## Agent Service API

Base URL: `https://agent.gympt.com` (prod) / `http://localhost:8001` (local)

### AI 운동 추천

**POST** `/api/v1/recommendations`

**Request:**
```json
{
  "user_id": 123,
  "user_profile": {
    "age": 30,
    "weight_kg": 75,
    "height_cm": 175,
    "fitness_level": "intermediate",
    "goals": ["muscle_gain", "strength"]
  },
  "workout_history": [
    {
      "date": "2026-05-18",
      "exercises": ["벤치프레스", "스쿼트"],
      "duration_minutes": 45
    }
  ],
  "preferences": {
    "workout_days_per_week": 4,
    "session_duration_minutes": 60,
    "equipment": ["barbell", "dumbbell", "machine"]
  }
}
```

**Response (200 OK):**
```json
{
  "recommendation_id": "rec_xyz789",
  "workout_plan": {
    "title": "4일 분할 근력 운동 프로그램",
    "description": "중급자를 위한 상하체 분할 루틴",
    "weeks": 4,
    "days": [
      {
        "day": "Monday",
        "focus": "상체 (가슴, 삼두)",
        "exercises": [
          {
            "name": "벤치프레스",
            "sets": 4,
            "reps": "8-10",
            "rest_seconds": 90,
            "notes": "점진적 과부하 원칙 적용"
          },
          {
            "name": "인클라인 덤벨 프레스",
            "sets": 3,
            "reps": "10-12",
            "rest_seconds": 60
          }
        ]
      }
    ]
  },
  "rationale": "현재 중급 수준에 맞춰 4일 분할 루틴을 추천합니다. 상체와 하체를 분리하여 각 근육군에 충분한 휴식을 제공합니다.",
  "confidence_score": 0.92,
  "created_at": "2026-05-19T12:00:00Z"
}
```

### AI 채팅

**POST** `/api/v1/chat`

**Request:**
```json
{
  "user_id": 123,
  "message": "오늘 운동 후 근육통이 심한데 어떻게 해야 하나요?",
  "context": {
    "last_workout_date": "2026-05-18",
    "last_workout_type": "leg_day"
  }
}
```

**Response (200 OK):**
```json
{
  "chat_id": "chat_123456",
  "response": "하체 운동 후 근육통(DOMS)은 정상적인 반응입니다. 다음을 권장합니다:\n\n1. 가벼운 유산소 운동 (걷기 10-15분)\n2. 스트레칭과 폼롤러\n3. 충분한 수분 섭취\n4. 단백질 섭취 (체중kg당 1.6-2.2g)\n5. 충분한 수면 (7-9시간)\n\n통증이 3-4일 이상 지속되거나 심해지면 전문의 상담을 권장합니다.",
  "suggestions": [
    "스트레칭 루틴 보기",
    "회복 운동 추천받기",
    "영양 가이드 보기"
  ],
  "created_at": "2026-05-19T12:00:00Z"
}
```

---

## Posture Analysis API

Base URL: `https://posture.gympt.com` (prod) / `http://localhost:8002` (local)

### 자세 분석 시작

**POST** `/api/v1/analyze/start`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "exercise_type": "squat",
  "kvs_stream_name": "kvs-stream-123"
}
```

**Response (200 OK):**
```json
{
  "analysis_id": "analysis_xyz",
  "session_id": "sess_abc123",
  "status": "analyzing",
  "websocket_url": "wss://posture.gympt.com/ws/session/sess_abc123",
  "started_at": "2026-05-19T12:00:00Z"
}
```

### WebSocket 연결 (실시간 피드백)

**WebSocket** `wss://posture.gympt.com/ws/session/{session_id}`

**클라이언트 → 서버 (Ping):**
```json
{
  "type": "ping"
}
```

**서버 → 클라이언트 (실시간 피드백):**
```json
{
  "type": "feedback",
  "timestamp": "2026-05-19T12:01:30Z",
  "exercise": "squat",
  "rep_count": 5,
  "pose_data": {
    "knee_angle_left": 95,
    "knee_angle_right": 93,
    "hip_angle": 85,
    "back_angle": 78
  },
  "feedback": [
    {
      "severity": "warning",
      "message": "무릎이 발끝보다 앞으로 나가고 있습니다",
      "correction": "무릎을 뒤로 당기세요"
    }
  ],
  "score": 85
}
```

**서버 → 클라이언트 (세트 완료):**
```json
{
  "type": "set_complete",
  "set_number": 1,
  "total_reps": 10,
  "average_score": 87,
  "feedback_summary": [
    "무릎 각도 개선 필요",
    "등 자세 양호"
  ]
}
```

---

## 에러 처리

### 표준 에러 응답

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "잘못된 요청 데이터",
    "details": [
      {
        "field": "email",
        "message": "유효한 이메일 형식이 아닙니다"
      }
    ],
    "timestamp": "2026-05-19T12:00:00Z",
    "path": "/api/v1/auth/signup"
  }
}
```

### HTTP 상태 코드

| Code | Description | 예시 |
|------|-------------|------|
| 200 | OK | 성공적인 GET 요청 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 삭제 성공 |
| 400 | Bad Request | 잘못된 요청 데이터 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 중복 (이미 존재하는 이메일 등) |
| 422 | Unprocessable Entity | 비즈니스 로직 오류 |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 서버 오류 |
| 503 | Service Unavailable | 서비스 일시 중단 |

### 에러 코드

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | 요청 데이터 검증 실패 |
| AUTHENTICATION_ERROR | 인증 실패 (잘못된 자격증명) |
| AUTHORIZATION_ERROR | 권한 없음 |
| NOT_FOUND | 리소스 없음 |
| CONFLICT | 리소스 충돌 (중복) |
| RATE_LIMIT_EXCEEDED | Rate limit 초과 |
| INTERNAL_ERROR | 서버 내부 오류 |

---

## Rate Limiting

### 제한 정책

| API | Limit | Window |
|-----|-------|--------|
| Auth (login, signup) | 10 requests | 15분 |
| General API | 1000 requests | 1시간 |
| AI Recommendations | 20 requests | 1시간 |
| WebSocket connections | 5 connections | 동시 |

### Rate Limit 헤더

**Response Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1684512000
```

**Rate Limit 초과 시:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "시간당 요청 한도를 초과했습니다",
    "retry_after_seconds": 3600
  }
}
```

---

## API 버전 관리

- **현재 버전:** v1
- **Base Path:** `/api/v1/`
- **버전 변경 시:** 최소 6개월 이전 공지, 이전 버전 병행 운영

---

**관련 문서:**
- [개발 가이드](개발가이드.md)
- [테스트 가이드](테스트가이드.md)

**API 문의:** Platform Team  
**최종 업데이트:** 2026-05-19
