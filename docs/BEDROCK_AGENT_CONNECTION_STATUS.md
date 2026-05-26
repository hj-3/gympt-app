# Bedrock Agent 연결 현황

**날짜**: 2026-05-26  
**상태**: Agent 생성 완료, 연결 작업 진행 중

## 완료된 작업

### 1. Bedrock Agent 생성 ✅
- **Agent ID**: `WPQ0RESSZS`
- **Agent Name**: `gympt-prod-pt-agent`
- **Agent Status**: `PREPARED`
- **Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Description**: AI PT 에이전트 - 운동 추천, 자세 피드백, 리포트 생성
- **Created**: 2026-05-25T16:42:09Z

### 2. Agent Alias 생성 ✅
- **Prod Alias ID**: `E5LE29XZS1`
- **Alias Name**: `prod`
- **Version**: `1`
- **Status**: `PREPARED`
- **Invocation State**: `ACCEPT_INVOCATIONS`

### 3. IAM Role Terraform 추가 ✅
**파일**: `terraform/modules/iam/main.tf`

생성된 리소스:
- `aws_iam_role.bedrock_agent_role` - Bedrock Agent service role
- `aws_iam_policy.bedrock_agent_inference` - Claude model 호출 권한
- `aws_iam_policy.bedrock_agent_s3` - S3 access (knowledge base)
- `aws_iam_policy.bedrock_agent_logs` - CloudWatch Logs

**현재 상태**: 커밋 완료 (commit: a8a6b77)

**적용 필요**:
```bash
cd gympt-infra/terraform/environments/prod
terraform plan -target=module.iam
terraform apply -target=module.iam
```

**Terraform Role ARN** (생성 예정):
```
arn:aws:iam::337112169365:role/gympt-prod-bedrock-role
```

### 4. Helm Values 업데이트 ✅
**파일**: `gympt-gitops/charts/agent-service/values-prod.yaml`

추가된 환경 변수:
```yaml
- name: BEDROCK_AGENT_ID
  value: "WPQ0RESSZS"
- name: BEDROCK_AGENT_ALIAS_ID
  value: "E5LE29XZS1"
- name: ENABLE_BEDROCK_MOCK
  value: "false"
```

**현재 상태**: GitOps 레포에 푸시 완료 (commit: 008d7c8)

---

## 진행 중인 작업

### 5. Bedrock Agent Role 교체 🔄
현재 Agent가 사용 중인 Role:
```
arn:aws:iam::337112169365:role/service-role/AmazonBedrockExecutionRoleForAgents_1MEMDMQA2OG
```

교체할 Role (Terraform 관리):
```
arn:aws:iam::337112169365:role/gympt-prod-bedrock-role
```

**교체 방법**:
1. Terraform apply로 `gympt-prod-bedrock-role` 생성
2. AWS Console → Bedrock → Agents → gympt-prod-pt-agent
3. Edit agent → Service role → `gympt-prod-bedrock-role` 선택
4. Prepare agent (새 버전 생성)
5. Alias 업데이트 (prod alias → 새 버전)

또는 AWS CLI:
```bash
# Terraform apply 후
ROLE_ARN=$(terraform output -raw bedrock_agent_role_arn)

aws bedrock-agent update-agent \
  --agent-id WPQ0RESSZS \
  --agent-name gympt-prod-pt-agent \
  --agent-resource-role-arn "$ROLE_ARN" \
  --region us-west-2

aws bedrock-agent prepare-agent \
  --agent-id WPQ0RESSZS \
  --region us-west-2

# 새 버전 확인
NEW_VERSION=$(aws bedrock-agent list-agent-versions --agent-id WPQ0RESSZS --region us-west-2 --query 'agentVersionSummaries[0].agentVersion' --output text)

# Alias 업데이트
aws bedrock-agent update-agent-alias \
  --agent-id WPQ0RESSZS \
  --agent-alias-id E5LE29XZS1 \
  --routing-configuration "agentVersion=$NEW_VERSION" \
  --region us-west-2
```

---

## 대기 중인 작업

### 6. ArgoCD 배포 ⏸️
**현황**: ArgoCD Application 미설정
- `kubectl get applications -n argocd` → No resources found
- Agent Service Pod 없음

**필요한 작업**:
ArgoCD를 통한 자동 배포가 설정되지 않은 상태입니다. 수동 배포 또는 ArgoCD 설정이 필요합니다.

**옵션 1: 수동 Helm 배포**
```bash
cd gympt-gitops/charts/agent-service
helm upgrade --install agent-service . \
  -f values-prod.yaml \
  -n gympt-prod \
  --create-namespace
```

**옵션 2: ArgoCD 설정**
ArgoCD Application 리소스 생성 필요

### 7. Knowledge Base 연결 ⏸️
현재 Agent는 Knowledge Base 없이 생성됨

**추후 작업**:
1. OpenSearch Serverless Collection 생성
2. S3에 운동 지식 문서 업로드
3. Knowledge Base 생성
4. Agent에 Knowledge Base 연결
5. Helm values에 `BEDROCK_KNOWLEDGE_BASE_ID` 추가

현재는 **Knowledge Base 없이 기본 Claude 모델만 사용**하여 테스트 가능

---

## 다음 단계

### 즉시 실행 가능

**1. Terraform IAM Role 적용**
```bash
cd gympt-infra/terraform/environments/prod

# 다른 세션의 lock 확인
terraform force-unlock <LOCK_ID>  # 필요시

terraform plan -target=module.iam
terraform apply -target=module.iam
```

**2. Bedrock Agent Role 교체**
Terraform apply 후 Agent의 Service Role을 Terraform이 생성한 role로 교체

**3. Agent Service 배포**
수동 Helm 배포 또는 ArgoCD 설정

**4. 테스트**
```bash
# Health check
curl https://agent.g2mpt.com/health

# Backend API를 통한 테스트
curl -X POST https://api.g2mpt.com/api/v1/agent/workout-recommendation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "userId": "test-001",
    "goal": "MUSCLE_GAIN",
    "fitnessLevel": "INTERMEDIATE",
    "daysPerWeek": 4
  }'
```

### 이후 작업

**5. Knowledge Base 연결** (선택)
- OpenSearch Serverless + 운동 지식 문서
- RAG 기반 근거 있는 추천

**6. 모니터링 설정**
- CloudWatch Logs 확인
- Bedrock API 호출 메트릭
- 비용 모니터링

**7. 프로덕션 최적화**
- 캐싱 전략
- Rate limiting
- Error handling

---

## 현재 구성 요약

```
┌─────────────────────────────────────────────────────────┐
│ Frontend (g2mpt.com)                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Backend API (api.g2mpt.com)                            │
│ - POST /api/v1/agent/workout-recommendation            │
│ - POST /api/v1/agent/posture-feedback                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Agent Service (EKS Pod)                                 │
│ Env:                                                     │
│   BEDROCK_AGENT_ID: WPQ0RESSZS                         │
│   BEDROCK_AGENT_ALIAS_ID: E5LE29XZS1                   │
│   ENABLE_BEDROCK_MOCK: false                           │
│ IAM Role: gympt-prod-agent-service-pod-role            │
│   - bedrock-agent-runtime:InvokeAgent ✅                │
│   - bedrock-agent-runtime:Retrieve ✅                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ AWS Bedrock Agent (us-west-2)                          │
│ Agent: gympt-prod-pt-agent (WPQ0RESSZS)                │
│ Alias: prod (E5LE29XZS1)                               │
│ Model: Claude 3.5 Sonnet v2                            │
│ IAM Role: gympt-prod-bedrock-role (교체 예정)          │
│   - bedrock:InvokeModel ✅                              │
│   - bedrock:GetInferenceProfile ✅                      │
│ Knowledge Base: 미연결 (추후 작업)                     │
└─────────────────────────────────────────────────────────┘
```

---

## 참고 문서

- [BEDROCK_AGENT_PRODUCTION_GUIDE.md](./BEDROCK_AGENT_PRODUCTION_GUIDE.md) - 전체 설정 가이드
- [BEDROCK_AGENT_CONNECTION_TASKS.md](./BEDROCK_AGENT_CONNECTION_TASKS.md) - 작업 체크리스트

---

## 문제 해결

### Terraform State Lock
```bash
# Lock ID 확인 후
echo "yes" | terraform force-unlock <LOCK_ID>
```

### Agent Service Pod 없음
ArgoCD 미설정 상태 - 수동 Helm 배포 필요

### IAM 권한 오류
Terraform role 적용 및 Agent role 교체 필요
