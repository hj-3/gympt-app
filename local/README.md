# GYMPT Local Development Environment

로컬 개발 환경을 위한 Docker Compose 기반 설정입니다.

## 📋 개요

이 디렉토리는 AWS 리소스를 로컬에서 시뮬레이션하는 개발 환경을 제공합니다.

## 🏗️ 구성

### Infrastructure Services

- **PostgreSQL 16**: 메인 데이터베이스
- **Redis 7**: 캐시 및 세션 스토어
- **LocalStack**: AWS 서비스 에뮬레이터
  - S3 (객체 스토리지)
  - SQS (메시지 큐)
  - DynamoDB (NoSQL 데이터베이스)
  - EventBridge (이벤트 버스)
  - SNS (알림)
  - Secrets Manager (시크릿 관리)

### Application Services

- **backend-api** (8080)
- **agent-service** (8001)
- **posture-analysis-service** (8002)
- **report-service** (8003)
- **notification-service** (8004)
- **remediation-worker**

### Observability Stack (선택사항)

- **Prometheus** (9090): 메트릭 수집
- **Grafana** (3001): 시각화
- **Loki** (3100): 로그 수집
- **Jaeger** (16686): 분산 추적

## 🚀 빠른 시작

```bash
# 전체 환경 시작
./scripts/local-up.sh

# 로그 확인
./scripts/local-logs.sh

# 환경 중지
./scripts/local-down.sh

# 완전 초기화
./scripts/local-reset.sh
```

## 📁 디렉토리 구조

```
local/
├── docker-compose.yml              # 메인 서비스
├── docker-compose.observability.yml # 관측성 스택
├── init/                           # 초기화 스크립트
│   ├── postgres/                   # PostgreSQL 초기화 SQL
│   ├── dynamodb/                   # DynamoDB 테이블 스키마
│   └── localstack/                 # LocalStack 초기화 스크립트
├── scripts/                        # 유틸리티 스크립트
│   ├── local-up.sh
│   ├── local-down.sh
│   ├── local-reset.sh
│   ├── local-logs.sh
│   └── local-seed.sh
└── configs/                        # 설정 파일
    ├── prometheus.yml
    └── grafana/
```

## 🔧 스크립트 상세

### local-up.sh

전체 로컬 환경을 시작합니다.

```bash
./scripts/local-up.sh
```

**수행 작업:**
1. Docker 및 Docker Compose 확인
2. .env 파일 확인 및 생성
3. 기존 컨테이너 중지
4. 인프라 서비스 시작 (PostgreSQL, Redis, LocalStack)
5. 서비스 헬스 체크
6. LocalStack 리소스 초기화
7. 애플리케이션 서비스 시작

### local-down.sh

모든 서비스를 중지합니다 (데이터 보존).

```bash
./scripts/local-down.sh
```

### local-reset.sh

모든 데이터를 삭제하고 환경을 초기화합니다.

```bash
./scripts/local-reset.sh
```

**주의:** 이 명령은 모든 데이터를 삭제합니다!

### local-logs.sh

서비스 로그를 확인합니다.

```bash
# 전체 로그
./scripts/local-logs.sh

# 특정 서비스
./scripts/local-logs.sh backend-api
./scripts/local-logs.sh agent-service
```

### local-seed.sh

테스트 데이터를 시드합니다.

```bash
./scripts/local-seed.sh
```

**생성되는 데이터:**
- 테스트 사용자
- 샘플 운동 데이터
- DynamoDB 이벤트

## 🔍 서비스 접속

### Application Services

| 서비스 | URL | 용도 |
|--------|-----|------|
| Backend API | http://localhost:8080 | REST API |
| Backend Swagger | http://localhost:8080/swagger-ui.html | API 문서 |
| Backend Health | http://localhost:8080/actuator/health | 헬스 체크 |
| Agent Service | http://localhost:8001 | AI 에이전트 |
| Agent Docs | http://localhost:8001/docs | API 문서 |
| Posture Analysis | http://localhost:8002 | 자세 분석 |
| Report Service | http://localhost:8003 | 리포트 생성 |
| Notification Service | http://localhost:8004 | 알림 |

### Infrastructure

| 서비스 | 접속 정보 | 용도 |
|--------|---------|------|
| PostgreSQL | localhost:5432 | 데이터베이스 |
| Redis | localhost:6379 | 캐시 |
| LocalStack | http://localhost:4566 | AWS 에뮬레이터 |
| DynamoDB Admin | http://localhost:8001 | DynamoDB UI |

### Observability (선택사항)

| 서비스 | URL | 인증 |
|--------|-----|------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3001 | admin/admin |
| Jaeger | http://localhost:16686 | - |

## 💾 데이터베이스 접근

### PostgreSQL

```bash
# psql로 접속
docker exec -it gympt-postgres psql -U gympt_user -d gympt

# 또는
psql -h localhost -p 5432 -U gympt_user -d gympt
```

### Redis

```bash
# redis-cli로 접속
docker exec -it gympt-redis redis-cli

# 또는
redis-cli -h localhost -p 6379
```

### DynamoDB

```bash
# AWS CLI로 접근
aws --endpoint-url=http://localhost:4566 dynamodb list-tables --region ap-northeast-2

# DynamoDB Admin UI
# http://localhost:8001
```

## 🧪 테스트

### API 테스트

```bash
# Backend API 헬스 체크
curl http://localhost:8080/actuator/health

# 사용자 등록
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gympt.com",
    "password": "test123",
    "name": "Test User"
  }'

# 로그인
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gympt.com",
    "password": "test123"
  }'
```

### LocalStack 테스트

```bash
# S3 버킷 확인
aws --endpoint-url=http://localhost:4566 s3 ls

# SQS 큐 확인
aws --endpoint-url=http://localhost:4566 sqs list-queues --region ap-northeast-2

# DynamoDB 테이블 확인
aws --endpoint-url=http://localhost:4566 dynamodb list-tables --region ap-northeast-2
```

## 🐛 트러블슈팅

### 포트 충돌

```bash
# 포트 사용 확인
lsof -i :8080

# 프로세스 종료
kill -9 <PID>
```

### 컨테이너 시작 실패

```bash
# 로그 확인
docker-compose logs <service-name>

# 컨테이너 재시작
docker-compose restart <service-name>

# 완전 재생성
docker-compose up -d --force-recreate <service-name>
```

### LocalStack 초기화 실패

```bash
# LocalStack 로그 확인
docker logs gympt-localstack

# LocalStack 재시작
docker-compose restart localstack

# 초기화 스크립트 수동 실행
./init/localstack/init-resources.sh
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 로그 확인
docker logs gympt-postgres

# PostgreSQL 재시작
docker-compose restart postgres

# 연결 테스트
docker exec gympt-postgres pg_isready -U gympt_user -d gympt
```

## 🔧 고급 설정

### 개별 서비스만 시작

```bash
# 인프라만 시작
docker-compose up -d postgres redis localstack

# 특정 서비스만 시작
docker-compose up -d backend-api
```

### 서비스 로그 레벨 변경

```bash
# docker-compose.yml에서 환경변수 수정
environment:
  LOG_LEVEL: DEBUG  # INFO, DEBUG, ERROR
```

### 관측성 스택 시작

```bash
# Prometheus, Grafana, Jaeger, Loki 시작
docker-compose -f docker-compose.observability.yml up -d

# 중지
docker-compose -f docker-compose.observability.yml down
```

### 볼륨 관리

```bash
# 볼륨 목록
docker volume ls | grep gympt

# 특정 볼륨 삭제
docker volume rm gympt-local_postgres_data

# 모든 볼륨 삭제 (주의!)
docker volume prune
```

## 📊 성능 모니터링

### 컨테이너 리소스 사용

```bash
# 실시간 리소스 모니터링
docker stats

# 특정 컨테이너만
docker stats gympt-backend-api gympt-postgres
```

### 메트릭 확인

Prometheus UI (http://localhost:9090)에서:

```promql
# CPU 사용률
container_cpu_usage_seconds_total

# 메모리 사용량
container_memory_usage_bytes

# HTTP 요청 수
http_requests_total

# 응답 시간
http_request_duration_seconds
```

## 🔄 개발 워크플로우

### 1. 환경 시작

```bash
cd local
./scripts/local-up.sh
```

### 2. 코드 수정

```bash
cd ../backend-api
# 코드 수정...
```

### 3. 로컬 테스트

```bash
# 단위 테스트
./gradlew test

# 또는 서비스 재빌드
cd ../local
docker-compose up -d --build backend-api
```

### 4. 로그 확인

```bash
./scripts/local-logs.sh backend-api
```

### 5. 환경 정리

```bash
./scripts/local-down.sh
```

## 📝 환경변수

로컬 환경에서 사용되는 주요 환경변수:

```env
# 환경
ENV=local

# 데이터베이스
DB_HOST=postgres
DB_PORT=5432
DB_NAME=gympt
DB_USER=gympt_user
DB_PASSWORD=gympt_local_pass

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# LocalStack
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localstack:4566
SQS_ENDPOINT_URL=http://localstack:4566
DYNAMODB_ENDPOINT_URL=http://localstack:4566

# Bedrock (Mock)
MOCK_BEDROCK=true
```

## 🔐 보안 주의사항

- 로컬 환경의 비밀번호는 약한 값 사용 (프로덕션 절대 사용 금지)
- `.env` 파일은 Git에 커밋하지 않음
- LocalStack의 AWS 자격증명은 `test/test` 사용 (실제 AWS와 격리)

## 📚 추가 리소스

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [LocalStack 문서](https://docs.localstack.cloud/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
- [Redis 문서](https://redis.io/documentation)

## 🤝 도움이 필요하신가요?

- Slack: #gympt-dev
- 문서: [메인 README](../README.md)
- 이슈: GitHub Issues
