# Bedrock Agent 테스트 가이드

**날짜**: 2026-05-26  
**Agent ID**: WPQ0RESSZS  
**Alias ID**: E5LE29XZS1

## 배포 현황 ✅

### 1. ArgoCD
```
agent-service-prod: Synced, Healthy
backend-api-prod: Synced, Degraded (1 old pod crashing)
```

### 2. Agent Service Pods
```
agent-service-prod-generic-worker: 3/3 Running
- BEDROCK_AGENT_ID: WPQ0RESSZS
- BEDROCK_AGENT_ALIAS_ID: E5LE29XZS1
- ENABLE_BEDROCK_MOCK: false
- BEDROCK_REGION: us-west-2
```

### 3. IAM 권한
- Terraform으로 `gympt-prod-bedrock-role` 생성 완료
- Agent에 role 연결 완료
- Pod role에 `bedrock-agent-runtime:InvokeAgent` 권한 있음

---

## 테스트 방법

### Option 1: Backend API를 통한 테스트 (권장)

**Endpoint**: `https://api.g2mpt.com/api/v1/agent/workout-recommendation`

#### 1. 토큰 발급 (필요시)
먼저 로그인하여 JWT 토큰을 받아야 합니다.

```bash
# 로그인
curl -X POST https://api.g2mpt.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'
```

#### 2. 운동 추천 API 호출

```bash
curl -X POST https://api.g2mpt.com/api/v1/agent/workout-recommendation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
    "userId": "test-user-001",
    "goal": "MUSCLE_GAIN",
    "fitnessLevel": "INTERMEDIATE",
    "daysPerWeek": 4,
    "equipmentAvailable": ["BARBELL", "DUMBBELL", "BENCH"],
    "injuriesOrLimitations": ""
  }' | jq
```

**예상 응답**:
```json
{
  "userId": "test-user-001",
  "recommendation": "주 4회 근육 증가 프로그램...",
  "exercises": [...],
  "cached": false,
  "generatedAt": "2026-05-26T17:15:00Z"
}
```

#### 3. 자세 피드백 API 호출

```bash
curl -X POST https://api.g2mpt.com/api/v1/agent/posture-feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
    "sessionId": "sess-12345",
    "exerciseName": "squat",
    "postureData": {
      "kneeAngle": 85,
      "hipAngle": 90,
      "backAngle": 45,
      "depth": "parallel"
    },
    "repCount": 5
  }' | jq
```

**예상 응답**:
```json
{
  "sessionId": "sess-12345",
  "feedback": "자세가 좋습니다! 무릎 각도가...",
  "postureScore": 85,
  "suggestions": [...],
  "generatedAt": "2026-05-26T17:15:00Z"
}
```

---

### Option 2: Pod 내부에서 직접 테스트

Backend API를 거치지 않고 Agent Service를 직접 호출합니다.

```bash
# Agent Service Pod에 접속
kubectl exec -it -n gympt-prod agent-service-prod-generic-worker-cf9645fdf-5gczt -- /bin/bash

# Python으로 테스트
python3 << 'EOF'
import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='us-west-2')

response = client.invoke_agent(
    agentId='WPQ0RESSZS',
    agentAliasId='E5LE29XZS1',
    sessionId='test-session-001',
    inputText='주 4회 운동할 수 있고 근육을 키우고 싶어요. 바벨과 덤벨이 있습니다. 운동 계획을 추천해주세요.'
)

# 스트리밍 응답 처리
output = ""
for event in response.get('completion', []):
    if 'chunk' in event:
        chunk = event['chunk']
        if 'bytes' in chunk:
            output += chunk['bytes'].decode('utf-8')

print(output)
EOF
```

---

### Option 3: AWS CLI로 직접 테스트

로컬에서 AWS CLI로 Agent를 직접 호출합니다.

```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id WPQ0RESSZS \
  --agent-alias-id E5LE29XZS1 \
  --session-id test-session-$(date +%s) \
  --input-text "주 3회 운동 가능하고 체중 감량이 목표입니다. 초보자 수준이에요. 홈트레이닝 루틴을 추천해주세요." \
  --region us-west-2 \
  --output text \
  --query 'completion'
```

---

## 테스트 시나리오

### 시나리오 1: 초보자 체중 감량
```json
{
  "goal": "WEIGHT_LOSS",
  "fitnessLevel": "BEGINNER",
  "daysPerWeek": 3,
  "equipmentAvailable": []
}
```

**검증 사항**:
- ✅ 초보자에 맞는 강도
- ✅ 체중 감량에 효과적인 운동
- ✅ 맨몸 운동 위주
- ✅ 안전 주의사항 포함

### 시나리오 2: 중급자 근육 증가
```json
{
  "goal": "MUSCLE_GAIN",
  "fitnessLevel": "INTERMEDIATE",
  "daysPerWeek": 4,
  "equipmentAvailable": ["BARBELL", "DUMBBELL", "BENCH"]
}
```

**검증 사항**:
- ✅ 중급자 수준의 볼륨
- ✅ 근비대 효과적인 운동
- ✅ 장비를 활용한 복합 운동
- ✅ 세트/횟수 명확히 제시

### 시나리오 3: 부상 있는 경우
```json
{
  "goal": "GENERAL_FITNESS",
  "fitnessLevel": "INTERMEDIATE",
  "daysPerWeek": 3,
  "equipmentAvailable": ["DUMBBELL"],
  "injuriesOrLimitations": "왼쪽 무릎에 가벼운 통증이 있습니다"
}
```

**검증 사항**:
- ✅ 무릎에 부담 적은 운동 추천
- ✅ 대체 운동 제시
- ✅ 부상 악화 방지 경고

---

## 예상 문제 및 해결

### 1. 403 Forbidden / Access Denied
**원인**: IAM 권한 부족

**확인**:
```bash
# Pod의 IAM role 확인
kubectl get sa agent-service -n gympt-prod -o yaml

# Role에 bedrock-agent-runtime 권한 확인
aws iam get-role-policy --role-name gympt-prod-agent-service-pod-role --policy-name gympt-prod-pod-bedrock-access
```

**해결**: Terraform apply로 권한 추가 (이미 완료)

### 2. Agent Not Found
**원인**: Agent ID 또는 Alias ID 잘못됨

**확인**:
```bash
aws bedrock-agent get-agent --agent-id WPQ0RESSZS --region us-west-2
aws bedrock-agent list-agent-aliases --agent-id WPQ0RESSZS --region us-west-2
```

### 3. Model Invocation Failed
**원인**: Bedrock Agent의 role이 Claude 모델 호출 권한 없음

**확인**:
```bash
aws iam get-role --role-name gympt-prod-bedrock-role
aws iam list-attached-role-policies --role-name gympt-prod-bedrock-role
```

**해결**: Terraform이 생성한 role에는 이미 권한 포함됨

### 4. 응답이 너무 느림 (>10초)
**원인**: 
- Agent가 PREPARING 상태
- Knowledge Base 연결 시 검색 시간
- 네트워크 지연

**확인**:
```bash
aws bedrock-agent get-agent --agent-id WPQ0RESSZS --region us-west-2 --query 'agent.agentStatus'
```

**해결**:
- Agent가 PREPARED 상태인지 확인
- 타임아웃 설정 조정 (backend-api: 30s)

### 5. Empty Response
**원인**: 스트리밍 응답 처리 오류

**확인**: Agent Service 로그 확인
```bash
kubectl logs -n gympt-prod -l app.kubernetes.io/name=agent-service --tail=100
```

---

## 성공 기준

### 기능 테스트
- ✅ Backend API → Agent Service → Bedrock Agent 호출 성공
- ✅ 한국어 응답 정상 생성
- ✅ 운동 계획이 구체적 (운동명, 세트, 횟수 포함)
- ✅ 안전 주의사항 포함
- ✅ 사용자 입력(목표, 레벨, 장비)을 반영

### 성능 테스트
- ✅ 응답 시간 < 10초
- ✅ 동시 요청 처리 (3 replicas)
- ✅ 캐싱 동작 확인 (Redis)

### 보안 테스트
- ✅ JWT 토큰 없이 호출 시 401
- ✅ IAM role 권한 정상 작동
- ✅ Cross-region inference 정상

---

## 모니터링

### CloudWatch Logs
```bash
# Agent 실행 로그
aws logs tail /aws/bedrock/agent/WPQ0RESSZS --follow --region us-west-2

# Agent Service 로그
kubectl logs -f -n gympt-prod -l app.kubernetes.io/name=agent-service
```

### Prometheus Metrics
- `agent_interactions_total{interaction_type="workout_recommend"}`
- `agent_interaction_duration_seconds`
- `bedrock_api_calls_total`
- `cache_hits_total`

---

## 다음 단계

### 1. Knowledge Base 연결 (선택)
현재는 기본 Claude 모델만 사용 중입니다. 운동 지식 기반을 추가하려면:

1. OpenSearch Serverless Collection 생성
2. S3에 운동 가이드 문서 업로드
3. Knowledge Base 생성
4. Agent에 연결
5. `BEDROCK_KNOWLEDGE_BASE_ID` 환경변수 추가

### 2. Frontend 통합
- 로그인 후 대시보드에서 "운동 추천" 버튼 클릭
- Backend API 호출 → Agent Service → Bedrock Agent
- 추천 결과를 UI에 표시

### 3. 실시간 자세 피드백
- WebRTC로 비디오 스트리밍
- Posture Analysis Service → Agent Service
- 실시간 피드백 생성

### 4. 리포트 생성
- 세션 완료 후 Report Service → Agent Service
- 운동 분석 및 개선점 제공

---

## 참고 문서

- [BEDROCK_AGENT_CONNECTION_STATUS.md](./BEDROCK_AGENT_CONNECTION_STATUS.md) - 연결 현황
- [BEDROCK_AGENT_PRODUCTION_GUIDE.md](./BEDROCK_AGENT_PRODUCTION_GUIDE.md) - 전체 가이드
