# GYMPT Database Management Guide

**Last Updated**: 2026-05-26

## Overview

GYMPT 플랫폼은 멀티 데이터베이스 아키텍처를 사용합니다:

- **PostgreSQL (RDS)**: 관계형 데이터 (users, workout_plans 등)
- **DynamoDB**: 이벤트 스트림 데이터 (workout sessions, posture events, agent interactions)
- **Redis (ElastiCache)**: 세션 캐시, API 응답 캐시

---

## 1. PostgreSQL (RDS)

### 1.1 인프라

**Production Environment**:
```
Endpoint: gympt-prod-postgres.crtplbjj0aoc.ap-northeast-2.rds.amazonaws.com
Database: gympt
Username: gymptadmin
Password: Kubernetes Secret (external-secrets/rds-credentials)
Instance: db.t3.large (2 vCPU, 8GB RAM)
Storage: 100GB GP3, encrypted
Multi-AZ: Yes
Backup: 30 days retention
```

**Terraform Configuration**: `gympt-infra/terraform/modules/rds/main.tf`

### 1.2 Schema Management: Flyway

**Flyway Configuration**:
- 자동 실행: Spring Boot 애플리케이션 시작 시
- Migration 위치: `backend-api/src/main/resources/db/migration/`
- Naming: `V{version}__{description}.sql` (예: `V3__Make_password_nullable.sql`)
- Baseline: 활성화 (`baseline-on-migrate: true`)
- 검증: Hibernate `ddl-auto: validate` (Flyway가 스키마 변경 담당)

**Production Application Config** (`application-prod.yml`):
```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: validate  # Flyway가 스키마 관리
  flyway:
    enabled: true
    baseline-on-migrate: true
```

### 1.3 Existing Migrations

#### V1__Initial_schema.sql
**Created**: Initial deployment  
**Purpose**: 초기 테이블 생성

주요 테이블:
- `users`: 사용자 정보 (Cognito 연동)
- `workout_plans`: 운동 계획
- `exercises`: 운동 데이터베이스
- `workout_sessions`: 세션 메타데이터 (DynamoDB와 매핑)
- `user_settings`: 사용자 설정

**Notable Constraints**:
- `users.password NOT NULL` ← Cognito 인증으로 변경 필요

#### V2__Add_ai_workout_fields.sql
**Created**: AI agent 기능 추가  
**Purpose**: AI 기반 운동 계획 지원

추가된 컬럼:
- `workout_plans.ai_generated`: AI 생성 여부 플래그
- `workout_plans.ai_reasoning`: AI 추천 근거
- `workout_plans.bedrock_session_id`: Bedrock Agent 세션 ID

#### V3__Make_password_nullable.sql
**Created**: 2026-05-26  
**Purpose**: Cognito 인증 전환 (비밀번호 DB 저장 제거)

```sql
-- Make password column nullable for Cognito authentication
-- Users authenticate via Cognito, so password is not stored in database

ALTER TABLE users ALTER COLUMN password DROP NOT NULL;
```

**Why**: 
- 사용자는 AWS Cognito에서 인증
- `password` 컬럼은 하위 호환성을 위해 유지하지만 NULL 허용
- `cognito_sub` 컬럼이 실제 인증 키

### 1.4 Creating New Migrations

**Step 1**: Create migration file
```bash
cd backend-api/src/main/resources/db/migration
touch V4__Your_description.sql
```

**Step 2**: Write SQL
```sql
-- Purpose: Add new column for feature X
-- Author: Your Name
-- Date: 2026-05-26

ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);
CREATE INDEX idx_users_phone ON users(phone_number);
```

**Step 3**: Test locally
```bash
cd backend-api
./gradlew bootRun --args='--spring.profiles.active=local'
# Check logs for Flyway execution
```

**Step 4**: Deploy
```bash
git add backend-api/src/main/resources/db/migration/V4__*.sql
git commit -m "Add V4 migration: your description"
git push origin main
```

**Step 5**: Monitor deployment
```bash
# GitHub Actions builds new image
# ArgoCD syncs new deployment
kubectl logs -n gympt-prod -l app.kubernetes.io/name=backend-api --tail=100 | grep -i flyway
```

**Step 6**: Verify migration
```sql
SELECT * FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 5;
```

### 1.5 Migration Best Practices

**DO**:
- ✅ 작고 독립적인 변경 단위로 migration 작성
- ✅ 주석으로 변경 이유 명시
- ✅ Index 생성 시 `CONCURRENTLY` 사용 (PostgreSQL)
- ✅ NOT NULL 추가 시 default 값 설정
- ✅ Local에서 먼저 테스트
- ✅ Rollback 가능한 변경 우선

**DON'T**:
- ❌ 이미 배포된 migration 파일 수정 (versioned, immutable)
- ❌ Large table에 즉시 NOT NULL 추가 (backfill 먼저)
- ❌ Production에서 직접 SQL 실행 (항상 Flyway 사용)
- ❌ DROP TABLE/COLUMN 없이 사전 협의
- ❌ Foreign key 추가 시 locking 고려 안 함

### 1.6 Troubleshooting

#### Migration 실행 안 됨
**Symptoms**: `flyway_schema_history` 테이블 없음, migration 로그 없음

**Check**:
1. Spring profile 확인: `application-prod.yml`에서 `spring.flyway.enabled: true`
2. Flyway dependency: `build.gradle`에 `org.flywaydb:flyway-core`
3. Startup logs: `kubectl logs -n gympt-prod <pod> | grep -i flyway`

**Fix**: `application-prod.yml` 수정 후 재배포

#### Migration 실패
**Symptoms**: Pod CrashLoopBackOff, "Migration checksum mismatch"

**Check**:
```sql
SELECT * FROM flyway_schema_history WHERE success = false;
```

**Fix**:
```sql
-- 실패한 migration 제거 (주의: production에서는 DBA와 협의)
DELETE FROM flyway_schema_history WHERE version = 'X' AND success = false;
```

#### Schema 불일치
**Symptoms**: "Schema validation failed"

**Check**:
- Entity 클래스와 DB 스키마 비교
- JPA `ddl-auto: validate` 모드에서 실패

**Fix**: 
- Migration 파일 추가로 스키마 동기화
- 절대 `ddl-auto: update` 사용하지 말 것 (production)

---

## 2. DynamoDB

### 2.1 인프라

**Tables** (Terraform managed):
```
gympt-prod-workout-sessions
gympt-prod-posture-events
gympt-prod-wearable-events
gympt-prod-agent-interactions
```

**Configuration**: `gympt-infra/terraform/modules/dynamodb/main.tf`

**Access**:
- Backend API: IRSA (Pod IAM role)
- Lambda Functions: Execution role

### 2.2 Data Model

#### workout-sessions
**Purpose**: 실시간 운동 세션 이벤트 스트림

```
PK: sessionId (String, UUID)
SK: timestamp (String, ISO8601)
Attributes:
  - userId: String
  - workoutPlanId: String (optional)
  - startTime: String
  - endTime: String (optional)
  - status: String (IN_PROGRESS, COMPLETED, ABANDONED)
  - totalDuration: Number (seconds)
  - caloriesBurned: Number
  - exercises: List<Map> (exercise log)
```

**TTL**: 90 days (cost optimization)

#### posture-events
**Purpose**: 자세 분석 이벤트 (ML 모델 출력)

```
PK: sessionId (String)
SK: timestamp#exerciseId (String)
Attributes:
  - userId: String
  - exerciseName: String
  - postureScore: Number (0-100)
  - keypoints: Map (body landmarks)
  - feedback: String
  - correctionSuggestions: List<String>
```

**GSI**: `userId-timestamp-index` (사용자별 자세 히스토리 조회)

#### agent-interactions
**Purpose**: Bedrock Agent 대화 히스토리

```
PK: userId (String)
SK: sessionId#timestamp (String)
Attributes:
  - agentId: String (WPQ0RESSZS)
  - agentAliasId: String (E5LE29XZS1)
  - inputText: String
  - outputText: String
  - interactionType: String (workout_recommend, posture_feedback, report_analysis)
  - tokenUsage: Map
  - latencyMs: Number
```

### 2.3 Best Practices

**DO**:
- ✅ 복합 sort key 사용 (`timestamp#exerciseId`)
- ✅ Sparse GSI로 특정 조건 쿼리 최적화
- ✅ Batch operations 사용 (BatchWriteItem)
- ✅ TTL 설정으로 오래된 데이터 자동 삭제
- ✅ DynamoDB Streams로 downstream processing (Lambda)

**DON'T**:
- ❌ Scan 사용 (Query로 대체)
- ❌ Hot partition (userId에만 의존)
- ❌ Large item (>400KB, S3 pointer 사용)
- ❌ 강한 일관성 요구 시 DynamoDB 선택

### 2.4 Monitoring

**CloudWatch Metrics**:
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `UserErrors` (throttling 확인)

**Alarms** (Terraform managed):
- User errors > 10/min

---

## 3. Redis (ElastiCache)

### 3.1 인프라

**Production Configuration**:
```
Cluster: gympt-prod-redis
Engine: Redis 7.0
Node type: cache.t3.medium
Nodes: 2 (primary + replica)
Multi-AZ: Yes
Auth token: Enabled (Kubernetes Secret)
Encryption: In-transit, at-rest
```

**Terraform**: `gympt-infra/terraform/modules/elasticache/main.tf`

### 3.2 Usage Patterns

#### Session Cache
**Key Pattern**: `session:{userId}:{sessionId}`  
**TTL**: 24 hours  
**Purpose**: WebSocket 세션 정보, 진행 중인 운동 상태

```redis
SET session:user123:sess456 "{\"status\":\"IN_PROGRESS\",\"startTime\":1716700000}"
EXPIRE session:user123:sess456 86400
```

#### API Response Cache
**Key Pattern**: `api:{endpoint}:{userId}:{params_hash}`  
**TTL**: 5-60 minutes (endpoint별 다름)  
**Purpose**: Dashboard 통계, 운동 추천 결과

```redis
SETEX api:dashboard:user123:today 300 "{\"totalWorkouts\":10,...}"
```

#### Rate Limiting
**Key Pattern**: `ratelimit:{userId}:{minute}`  
**TTL**: 60 seconds  
**Purpose**: API rate limiting (60 req/min)

```redis
INCR ratelimit:user123:202605261430
EXPIRE ratelimit:user123:202605261430 60
```

### 3.3 Eviction Policy

**Config**: `allkeys-lru`
- 메모리 부족 시 가장 오래 사용하지 않은 key 제거
- 명시적 TTL 없이도 자동 정리

### 3.4 Monitoring

**CloudWatch Metrics**:
- `CacheHitRate` (>90% 목표)
- `CurrConnections` (leak 확인)
- `DatabaseMemoryUsagePercentage` (<80% 유지)

**Health Check**:
```bash
kubectl exec -n gympt-prod <pod> -- redis-cli -h $REDIS_HOST --tls --askpass ping
# PONG 응답 확인
```

---

## 4. Backup and Disaster Recovery

### 4.1 PostgreSQL (RDS)

**Automated Backups**:
- 매일 스냅샷 (30일 보관)
- Point-in-time recovery (PITR): 최근 30일 내 어느 시점이든 복구 가능
- Backup window: 03:00-04:00 UTC

**Manual Snapshot**:
```bash
aws rds create-db-snapshot \
  --db-instance-identifier gympt-prod-postgres \
  --db-snapshot-identifier gympt-manual-$(date +%Y%m%d-%H%M%S)
```

**Restore**:
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier gympt-prod-postgres-restored \
  --db-snapshot-identifier gympt-manual-20260526-120000
```

### 4.2 DynamoDB

**On-Demand Backups**:
- AWS Backup service (Terraform managed)
- 90 days retention

**Point-in-Time Recovery (PITR)**:
- 활성화됨 (Terraform: `point_in_time_recovery = true`)
- 최근 35일 내 복구 가능

**Export to S3**:
```bash
aws dynamodb export-table-to-point-in-time \
  --table-arn arn:aws:dynamodb:ap-northeast-2:337112169365:table/gympt-prod-workout-sessions \
  --s3-bucket gympt-prod-backups-337112169365 \
  --s3-prefix dynamodb-exports/workout-sessions/
```

### 4.3 Redis (ElastiCache)

**Automated Snapshots**:
- 매일 스냅샷 (7일 보관)
- Terraform: `snapshot_retention_limit = 7`

**Manual Snapshot**:
```bash
aws elasticache create-snapshot \
  --replication-group-id gympt-prod-redis \
  --snapshot-name gympt-redis-manual-$(date +%Y%m%d)
```

**Note**: Redis는 캐시이므로 데이터 손실 시 애플리케이션이 자동으로 재생성

---

## 5. Migration Checklist

### 5.1 Before Deployment

- [ ] Local 환경에서 migration 테스트 완료
- [ ] Migration SQL 리뷰 완료 (팀원 확인)
- [ ] Rollback plan 수립 (필요 시)
- [ ] 영향 받는 서비스 파악 (downtime 필요 여부)
- [ ] Staging 환경 배포 및 검증 (if exists)

### 5.2 During Deployment

- [ ] GitHub Actions build 성공 확인
- [ ] ArgoCD sync 실행
- [ ] Pod startup logs 모니터링 (Flyway 실행 확인)
- [ ] `flyway_schema_history` 테이블 확인
- [ ] Health check 통과 확인 (`/actuator/health`)

### 5.3 After Deployment

- [ ] Integration tests 실행
- [ ] Frontend 주요 기능 테스트 (로그인, 대시보드, 세션 시작)
- [ ] CloudWatch metrics 모니터링 (error rate, latency)
- [ ] Rollback 준비 상태 유지 (최소 1시간)

---

## 6. Access and Security

### 6.1 Production DB Access

**Principle**: Production DB는 직접 접근 금지, 필요 시 read-only replica 사용

**Emergency Access** (DBA only):
```bash
# Bastion host를 통한 접근 (SSM Session Manager)
aws ssm start-session --target i-XXXXXXXXX  # Bastion instance ID

# Read-only replica 연결
psql -h gympt-prod-postgres-ro.crtplbjj0aoc.ap-northeast-2.rds.amazonaws.com -U gymptadmin -d gympt
```

**Pod-level Access** (troubleshooting only):
```bash
kubectl run -n gympt-prod psql-client --rm -it --image=postgres:17 -- \
  psql -h $DB_HOST -U $DB_USERNAME -d $DB_NAME
```

### 6.2 Secrets Management

**External Secrets Operator**:
- AWS SSM Parameter Store → Kubernetes Secret
- Auto-rotation: 90 days

**Secret Paths**:
```
/gympt/prod/rds/master-password
/gympt/prod/redis/auth-token
/gympt/prod/jwt/secret
```

**Rotation Process**:
1. AWS SSM에서 새 secret 생성
2. External Secrets Operator가 자동으로 Kubernetes Secret 업데이트
3. Pod restart (rollout restart)

---

## 7. Performance Optimization

### 7.1 PostgreSQL

**Indexes**:
```sql
-- 기존 indexes (V1 migration)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_cognito_sub ON users(cognito_sub);
CREATE INDEX idx_workout_sessions_user ON workout_sessions(user_id, start_time DESC);

-- Performance tip: EXPLAIN ANALYZE로 쿼리 최적화
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

**Connection Pooling**:
- HikariCP (Spring Boot default)
- Max pool size: 30 (production)
- Timeout: 20s

### 7.2 DynamoDB

**Capacity Mode**: On-demand (auto-scaling)
- 예측 불가능한 트래픽 패턴
- Cost-effective for current scale

**Hot Partition 방지**:
- Composite sort key 사용
- Write sharding (sessionId에 random suffix)

### 7.3 Redis

**Pipeline**: 여러 명령을 batch로 전송
```java
RedisTemplate<String, String> redisTemplate;
redisTemplate.executePipelined(new SessionCallback<Object>() {
    @Override
    public Object execute(RedisOperations operations) {
        operations.opsForValue().set("key1", "value1");
        operations.opsForValue().set("key2", "value2");
        return null;
    }
});
```

**Lua Script**: Atomic operations
```lua
-- Rate limiting script
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local current = redis.call('incr', key)
if current == 1 then
    redis.call('expire', key, 60)
end
return current <= limit
```

---

## 8. Monitoring and Alerts

### 8.1 Key Metrics

**PostgreSQL**:
- `DatabaseConnections` (CloudWatch)
- `ReadLatency`, `WriteLatency`
- `FreeStorageSpace` (<20GB 경고)

**DynamoDB**:
- `UserErrors` (throttling)
- `SystemErrors` (AWS issues)
- `ConsumedReadCapacityUnits`

**Redis**:
- `CacheHitRate` (<90% 경고)
- `Evictions` (메모리 부족 시그널)
- `ReplicationLag` (replica 지연)

### 8.2 Alarms (SNS → Slack)

Terraform managed (`gympt-infra/terraform/modules/monitoring/main.tf`):
- RDS CPU > 80% (5분)
- RDS storage < 20GB
- DynamoDB user errors > 10/min
- Redis memory > 80%

---

## 9. FAQ

### Q1: Migration 실패 시 어떻게 하나요?
**A**: Flyway는 실패 시 rollback하지 않습니다. `flyway_schema_history`에서 실패 record 확인 후:
1. SQL 오류 수정
2. 실패한 record 삭제 (또는 `flyway repair`)
3. 재배포

### Q2: 긴급하게 DB 스키마 변경이 필요합니다
**A**: 
1. **절대 수동 변경 금지** (Flyway가 checksum mismatch 감지)
2. 긴급 migration 파일 생성 → PR → 빠른 리뷰 → 배포
3. 5분 이내 배포 가능 (GitHub Actions + ArgoCD)

### Q3: DynamoDB scan이 너무 느립니다
**A**: 
- Scan은 anti-pattern, Query로 변경
- GSI 추가 필요 시 Terraform 수정 → apply
- 일회성 분석은 S3 export → Athena 사용

### Q4: Redis cache가 자주 miss 됩니다
**A**:
- TTL이 너무 짧은지 확인
- Eviction policy 확인 (`allkeys-lru`)
- Memory 부족 시 node type 업그레이드 (Terraform)

### Q5: Production DB 직접 접근이 필요합니다
**A**:
- **Read-only 작업**: Read replica 사용
- **Write 작업**: Migration 파일 작성 (Flyway)
- **긴급 수정**: DBA 승인 후 bastion host 경유

---

## 10. References

**Terraform Modules**:
- RDS: `gympt-infra/terraform/modules/rds/`
- DynamoDB: `gympt-infra/terraform/modules/dynamodb/`
- ElastiCache: `gympt-infra/terraform/modules/elasticache/`

**Application Code**:
- Backend API: `gympt-app/backend-api/`
- Migration files: `backend-api/src/main/resources/db/migration/`

**Related Docs**:
- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) - Full AWS architecture
- [BEDROCK_AGENT_TEST.md](./BEDROCK_AGENT_TEST.md) - Agent Service integration

**Useful Commands**:
```bash
# Flyway history
kubectl exec -n gympt-prod <pod> -- \
  psql $DB_HOST -U $DB_USERNAME -d $DB_NAME \
  -c "SELECT * FROM flyway_schema_history ORDER BY installed_rank;"

# DynamoDB item count
aws dynamodb describe-table --table-name gympt-prod-workout-sessions \
  --query 'Table.ItemCount'

# Redis info
kubectl exec -n gympt-prod <pod> -- \
  redis-cli -h $REDIS_HOST --tls --askpass info stats
```

---

**Maintainer**: HJ 
**Contact**: platform@gympt.example.com
