# Lambda, SQS, Bedrock 통합 분석 리포트

## 📊 Executive Summary

### 현재 상태
- ✅ **Lambda Functions**: 8개 모두 배포됨
- ✅ **SQS Queues**: 14개 (각 Lambda당 Queue + DLQ) 생성됨
- ✅ **Event Source Mappings**: 모든 Lambda가 SQS와 연결됨
- ❌ **Bedrock Agent**: 생성되지 않음
- ❌ **Knowledge Base**: 생성되지 않음
- ⚠️ **Agent Service**: Mock 모드로 동작 중

---

## 1️⃣ Lambda Functions 상태

### 배포된 Lambda Functions (8개)

| Lambda Function | SQS Trigger | Status | Purpose |
|----------------|-------------|---------|---------|
| `gympt-prod-agent-action` | ❌ None (Bedrock Agent 호출용) | ✅ Deployed | Bedrock Agent Action Group Handler |
| `gympt-prod-report-generator` | ✅ report-generation-queue | ✅ Enabled | AI 리포트 생성 |
| `gympt-prod-posture-event-processor` | ✅ posture-event-queue | ✅ Enabled | 자세 이벤트 처리 |
| `gympt-prod-thumbnail-generator` | ✅ thumbnail-generation-queue | ✅ Enabled | 비디오 썸네일 생성 |
| `gympt-prod-wearable-sync` | ✅ wearable-sync-queue | ✅ Enabled | 웨어러블 데이터 동기화 |
| `gympt-prod-recommendation-update` | ✅ recommendation-update-queue | ✅ Enabled | 운동 강도 조정 |
| `gympt-prod-notification` | ✅ notification-queue | ✅ Enabled | 멀티채널 알림 |
| `gympt-prod-export` | ✅ export-queue | ✅ Enabled | 데이터 내보내기 |

### Lambda 환경변수 확인

**agent-action Lambda:**
```bash
ENV=prod
LOG_LEVEL=INFO
REGION=ap-northeast-2
```

⚠️ **문제점**: Bedrock Agent ID가 환경변수에 없음

---

## 2️⃣ SQS Queues 상태

### 생성된 Queue (14개)

| Queue Name | Purpose | Lambda Consumer | DLQ |
|-----------|---------|----------------|-----|
| `gympt-prod-report-generation-queue` | 리포트 생성 요청 | report-generator | ✅ |
| `gympt-prod-posture-event-queue` | 자세 분석 이벤트 | posture-event-processor | ✅ |
| `gympt-prod-thumbnail-generation-queue` | 썸네일 생성 요청 | thumbnail-generator | ✅ |
| `gympt-prod-wearable-sync-queue` | 웨어러블 데이터 | wearable-sync | ✅ |
| `gympt-prod-recommendation-update-queue` | 추천 업데이트 | recommendation-update | ✅ |
| `gympt-prod-notification-queue` | 알림 발송 | notification | ✅ |
| `gympt-prod-export-queue` | 데이터 내보내기 | export | ✅ |

### Event Source Mappings 확인

모든 Lambda가 **Enabled** 상태로 SQS와 연결되어 있습니다.

```bash
posture-event-processor     → Enabled
wearable-sync              → Enabled
recommendation-update      → Enabled
notification               → Enabled
thumbnail-generator        → Enabled
report-generator           → Enabled
```

✅ **결론**: Lambda ↔ SQS 통합은 **정상 작동 가능 상태**입니다.

---

## 3️⃣ Bedrock 상태

### Bedrock Agent

**현재 상태:**
```bash
$ aws bedrock-agent list-agents --region us-west-2
{
    "agentSummaries": []
}
```

❌ **Bedrock Agent가 생성되지 않았습니다.**

### Knowledge Base

```bash
$ aws bedrock-agent list-knowledge-bases --region us-west-2
{
    "knowledgeBaseSummaries": []
}
```

❌ **Knowledge Base가 생성되지 않았습니다.**

### Bedrock Foundation Models

✅ Claude 모델 접근 가능:
- `anthropic.claude-3-5-sonnet-20241022-v2:0` (현재 agent-service 설정)
- `anthropic.claude-sonnet-4-5-20250929-v1:0`
- `anthropic.claude-opus-4-7`

---

## 4️⃣ Agent Service 현재 동작 방식

### 설정 (agent-service/app/config.py)

```python
bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
bedrock_agent_id: Optional[str] = None            # ❌ 없음
bedrock_agent_alias_id: Optional[str] = None      # ❌ 없음
bedrock_knowledge_base_id: Optional[str] = None   # ❌ 없음
enable_bedrock_mock: bool = True                  # ⚠️ Mock 모드
```

### 현재 동작 방식

#### Option 1: Direct Bedrock Runtime (현재 사용 중)
```
Frontend → Backend API → Agent Service → Bedrock Runtime (직접 호출)
```

- Bedrock **Runtime API**를 직접 호출 (`invoke_model`)
- **Agent는 사용하지 않음**
- RAG/Knowledge Base 없음
- 단순 프롬프트 → 응답 패턴

#### Option 2: Bedrock Agent (구현되어 있지만 미사용)
```
Frontend → Backend API → Agent Service → Bedrock Agent → Action Group (Lambda)
                                                       → Knowledge Base (RAG)
```

---

## 5️⃣ Bedrock Agent vs Runtime 비교

### Bedrock Runtime API (현재 방식)

**장점:**
- ✅ 간단한 구현 (Agent 생성 불필요)
- ✅ 즉시 사용 가능
- ✅ Terraform 관리 불필요
- ✅ 비용 효율적 (Agent 추가 비용 없음)

**단점:**
- ❌ RAG (Knowledge Base) 없음
- ❌ Action Group (외부 API 호출) 수동 구현 필요
- ❌ 대화 세션 관리 직접 구현
- ❌ Guardrails 수동 구현

### Bedrock Agent (고급 방식)

**장점:**
- ✅ Knowledge Base 연동 (RAG)
- ✅ Action Groups로 Lambda/API 호출
- ✅ 세션 관리 자동
- ✅ Guardrails 내장
- ✅ Prompt Orchestration

**단점:**
- ❌ Agent 생성/관리 필요
- ❌ Knowledge Base 구축 필요 (S3 + OpenSearch/Vector DB)
- ❌ 추가 비용 (Agent 호출당 요금)
- ❌ Terraform으로 관리하기 복잡

---

## 6️⃣ 현재 사용 중인 방식 확인

### Agent Service 코드 분석

`agent-service/app/clients/bedrock_client.py`:

```python
async def invoke_model(self, prompt: str, ...) -> Dict[str, Any]:
    """Direct Bedrock Runtime API 호출"""
    
    response = self.runtime_client.invoke_model(
        modelId=self.model_id,
        body=json.dumps(body),
        ...
    )
```

**결론: Runtime API를 직접 사용하고 있음** ✅

### Mock 모드 확인

`enable_bedrock_mock: bool = True`

⚠️ **현재 프로덕션에서도 Mock 모드일 가능성 높음**

확인 필요:
```bash
kubectl get deployment agent-service -n gympt-prod -o yaml | grep -A 5 "env:"
```

---

## 7️⃣ 문제 진단

### Q1: Bedrock Agent가 없어서 못 사용하고 있는가?

**답변: 아니오** ❌

- Agent Service는 **Runtime API**를 사용
- Agent 없이도 정상 동작 가능
- 현재 문제는 **Mock 모드 설정** 때문

### Q2: Agent Service가 정상 동작하지 않는 이유?

**원인:**
1. `enable_bedrock_mock: bool = True` (Mock 모드)
2. Production 환경변수에 `ENABLE_BEDROCK_MOCK=false` 미설정
3. IAM 권한 미확인

### Q3: Lambda들이 SQS와 정상 연결되어 있는가?

**답변: 예** ✅

- 모든 Event Source Mapping이 `Enabled` 상태
- Queue → Lambda 연결 정상
- DLQ 설정 완료

---

## 8️⃣ Bedrock Agent/KB를 Terraform으로 관리해야 하는가?

### Terraform으로 관리 가능 여부

#### ✅ 관리 가능한 리소스
- IAM Role (이미 구현됨)
- S3 Bucket (Knowledge Base 데이터)
- OpenSearch Serverless (Vector DB)

#### ⚠️ 제한적 지원
- **Bedrock Agent**: `aws_bedrockagent_agent` (2024년 이후 지원)
- **Knowledge Base**: `aws_bedrockagent_knowledge_base`
- **Action Group**: 수동 설정 필요

### 권장 방식

#### Option 1: Terraform 완전 관리 (권장하지 않음)

**단점:**
- Terraform Provider 성숙도 낮음
- Agent 업데이트 복잡
- Prompt 템플릿 관리 어려움

#### Option 2: 하이브리드 (추천) ✅

**Terraform로 관리:**
- IAM Role
- S3 Bucket
- OpenSearch Serverless
- Lambda Functions

**수동/Console로 관리:**
- Bedrock Agent 생성
- Knowledge Base 생성
- Action Group 설정
- Prompt 템플릿

#### Option 3: Bedrock Agent 사용하지 않음 (현재 방식) ✅✅ **최고 추천**

**이유:**
- Agent 없이도 모든 기능 구현 가능
- 관리 포인트 최소화
- 비용 절감
- Runtime API만으로 충분

---

## 9️⃣ 해결 방안

### 즉시 해결: Agent Service Mock 모드 해제

#### Step 1: Helm Values 업데이트

`gympt-gitops/charts/agent-service/values-prod.yaml`:

```yaml
env:
  - name: ENABLE_BEDROCK_MOCK
    value: "false"
  - name: BEDROCK_REGION
    value: "us-west-2"
  - name: BEDROCK_MODEL_ID
    value: "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

#### Step 2: IAM 권한 확인

Agent Service Pod Role에 Bedrock 권한 추가:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
  ]
}
```

#### Step 3: 재배포 및 테스트

```bash
# GitOps 푸시
git add charts/agent-service/values-prod.yaml
git commit -m "feat: Enable real Bedrock for agent-service"
git push

# ArgoCD Sync 대기
# 테스트: AI 추천 받기
```

---

## 🔟 장기 개선 사항

### 1. Knowledge Base (RAG) 추가 (선택)

**필요한 경우:**
- 운동 매뉴얼/가이드 문서가 많을 때
- 사용자 질문에 정확한 답변 필요
- 전문 지식 base 필요

**구성:**
1. S3에 문서 업로드 (Markdown/PDF)
2. OpenSearch Serverless 생성
3. Knowledge Base 생성 (Console)
4. Agent Service에서 `retrieve_from_knowledge_base()` 사용

**비용:**
- OpenSearch Serverless: ~$700/월
- Knowledge Base 검색: 요청당 과금

### 2. Bedrock Agent 도입 (선택)

**필요한 경우:**
- Action Group으로 복잡한 워크플로우 필요
- Guardrails로 안전장치 필요
- 대화 세션 관리 자동화

**구성:**
1. Console에서 Agent 생성
2. Action Group에 `agent-action` Lambda 연결
3. Agent ID를 환경변수로 주입
4. Agent Service에서 `invoke_agent()` 사용

---

## 📋 최종 권장사항

### 현재 아키텍처 유지 (추천) ✅

```
Frontend → Backend API → Agent Service → Bedrock Runtime API
                                       ↓
                                    DynamoDB (interaction log)
                                       ↓
                                    Redis (cache)
```

**이유:**
- ✅ 간단하고 명확
- ✅ 비용 효율적
- ✅ 관리 포인트 최소
- ✅ Lambda + SQS는 정상 작동
- ✅ Bedrock Runtime만으로 충분

### 당장 해야 할 일

1. **Agent Service Mock 모드 해제** (최우선)
2. **IAM 권한 확인 및 추가**
3. **Agent Service 재배포**
4. **AI 추천 기능 테스트**

### 하지 않아도 되는 일

1. ❌ Bedrock Agent 생성
2. ❌ Knowledge Base 구축
3. ❌ Terraform으로 Agent 관리

---

## 📈 테스트 시나리오

### 1. Lambda + SQS 테스트

```bash
# SQS에 메시지 발송
aws sqs send-message \
  --queue-url https://sqs.ap-northeast-2.amazonaws.com/337112169365/gympt-prod-report-generation-queue \
  --message-body '{"user_id": "test-user", "session_id": "test-session"}'

# Lambda 로그 확인
aws logs tail /aws/lambda/gympt-prod-report-generator --follow
```

### 2. Agent Service 테스트

```bash
# Backend API를 통해 AI 추천 요청
curl -X POST https://api.g2mpt.com/api/v1/agent/workout-recommendation \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "goal": "MUSCLE_GAIN",
    "fitness_level": "INTERMEDIATE",
    "days_per_week": 4
  }'
```

### 3. End-to-End 플로우

1. Frontend에서 AI 추천 요청
2. Backend API → Agent Service 호출
3. Agent Service → Bedrock Runtime 호출
4. 응답 캐싱 (Redis)
5. 상호작용 로깅 (DynamoDB)
6. Frontend에 추천 표시

---

## 🔗 관련 문서

- [Lambda Implementation Summary](../lambdas/IMPLEMENTATION_SUMMARY.md)
- [Agent Service README](../agent-service/README.md)
- [Bedrock Module](../../gympt-infra/terraform/modules/bedrock/)
- [API Gateway Pattern](./API_GATEWAY_PATTERN.md)

---

## ✅ 체크리스트

### Lambda + SQS
- [x] Lambda Functions 배포 완료
- [x] SQS Queues 생성 완료
- [x] Event Source Mappings 설정 완료
- [x] DLQ 설정 완료
- [ ] 실제 메시지 처리 테스트 필요

### Bedrock
- [x] Runtime API 접근 가능
- [x] Claude 모델 사용 가능
- [ ] Mock 모드 해제 필요
- [ ] IAM 권한 확인 필요
- [x] Agent 생성 불필요 (현재 아키텍처에서)
- [x] Knowledge Base 생성 불필요 (현재 아키텍처에서)

### Agent Service
- [x] 코드 구현 완료
- [x] Kubernetes 배포 완료
- [ ] Mock 모드 해제 필요
- [ ] 프로덕션 테스트 필요
