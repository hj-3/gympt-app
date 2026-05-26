# Bedrock Agent 연결 작업 체크리스트

콘솔에서 Bedrock Agent 생성 완료 후 진행해야 할 작업들을 정리합니다.

## 1. Bedrock Agent 콘솔 생성 (수동)

### 1.1 OpenSearch Serverless Collection 생성
- Collection name: `gympt-prod-exercise-knowledge`
- Collection type: Vector search
- Vector dimensions: 1024 (Titan Embeddings v2)
- Distance metric: Cosine similarity
- Network access: VPC endpoint 또는 Public
- Data access policy: IAM role 기반

### 1.2 S3 버킷에 지식 문서 업로드
- Bucket: `gympt-prod-media-337112169365`
- Prefix: `knowledge-base/exercises/`
- 파일 형식: PDF, TXT, Markdown
- 추천 컨텐츠:
  - 운동 가이드 (스쿼트, 데드리프트, 벤치프레스 등)
  - 영양 가이드 (단백질, 탄수화물, 식단 플랜)
  - 부상 예방 가이드
  - 회복 및 스트레칭 가이드

### 1.3 Knowledge Base 생성
- Name: `gympt-prod-exercise-kb`
- Description: "운동 지식 베이스 - 운동 가이드, 영양, 부상 예방"
- Embedding model: `amazon.titan-embed-text-v2:0`
- Data source: S3 (`s3://gympt-prod-media-337112169365/knowledge-base/exercises/`)
- Chunking strategy: Default (300 tokens with 20% overlap)
- OpenSearch collection: `gympt-prod-exercise-knowledge`

### 1.4 Bedrock Agent 생성
- Agent name: `gympt-prod-pt-agent`
- Model: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Description: "AI PT 에이전트 - 운동 추천, 자세 피드백, 리포트 생성"
- System prompt:
```
당신은 전문 퍼스널 트레이너 AI 어시스턴트입니다.

역할:
- 사용자의 운동 목표와 신체 정보를 기반으로 맞춤형 운동 계획을 제공합니다
- 실시간 자세 분석 데이터를 받아 즉각적인 피드백을 제공합니다
- 운동 세션 후 종합 리포트를 생성하고 개선 방향을 제시합니다
- 지식 베이스의 운동 관련 정보를 활용하여 근거 있는 조언을 제공합니다

지침:
1. 항상 사용자의 안전을 최우선으로 고려하세요
2. 부상 위험이 있는 경우 명확히 경고하세요
3. 지식 베이스의 정보를 인용하여 신뢰성을 높이세요
4. 한국어로 친근하고 전문적인 톤으로 응답하세요
5. 운동 강도는 사용자의 피트니스 레벨에 맞게 조정하세요

출력 형식:
- 운동 추천: 주차별 플랜, 운동명, 세트/횟수, 휴식 시간
- 자세 피드백: 점수(0-100), 개선점, 격려 메시지
- 리포트: 성과 요약, 진전 사항, 다음 목표
```

### 1.5 Action Groups 연결 (선택)
현재 단계에서는 Knowledge Base만 사용하고, 추후 필요시 Lambda Action Groups 추가:
- `getUserProfile`: 사용자 프로필 조회
- `getWorkoutHistory`: 운동 기록 조회
- `saveWorkoutSession`: 세션 저장

### 1.6 Agent Alias 생성
- Alias name: `prod`
- Description: "Production alias for PT Agent"

---

## 2. Terraform IAM 정책 적용

Bedrock Agent 권한을 Terraform으로 관리합니다.

```bash
cd /mnt/c/Users/gandd/OneDrive/Desktop/gympt/gympt-infra/terraform/environments/prod

# IAM 변경사항 확인
terraform plan -target=module.iam

# 적용
terraform apply -target=module.iam
```

**적용 내용:**
- `bedrock:InvokeModel` - Claude 모델 호출 권한
- `bedrock:InvokeModelWithResponseStream` - 스트리밍 응답 권한
- `bedrock-agent-runtime:InvokeAgent` - Bedrock Agent 호출 권한
- `bedrock-agent-runtime:Retrieve` - Knowledge Base 검색 권한

적용 대상: `gympt-prod-agent-service-pod-role`

---

## 3. Helm Values 업데이트

콘솔에서 생성한 Agent ID와 Alias ID를 Helm values에 추가합니다.

### 3.1 agent-service values-prod.yaml 수정

파일: `/mnt/c/Users/gandd/OneDrive/Desktop/gympt/gympt-gitops/charts/agent-service/values-prod.yaml`

추가할 환경 변수:
```yaml
env:
  # Bedrock Agent Configuration
  - name: BEDROCK_AGENT_ID
    value: "<YOUR_AGENT_ID>"  # 예: ABCD1234EF
  - name: BEDROCK_AGENT_ALIAS_ID
    value: "<YOUR_AGENT_ALIAS_ID>"  # 예: TSTALIASID
  - name: BEDROCK_KNOWLEDGE_BASE_ID
    value: "<YOUR_KB_ID>"  # 예: KB1234567890
  - name: ENABLE_BEDROCK_MOCK
    value: "false"  # Mock 모드 비활성화
```

Agent ID 확인 방법:
1. AWS Console → Bedrock → Agents
2. 생성한 Agent 클릭
3. Agent overview에서 Agent ID 복사
4. Aliases 탭에서 Alias ID 복사
5. Working drafts 탭에서 Knowledge Base ID 복사

### 3.2 GitOps 배포

```bash
cd /mnt/c/Users/gandd/OneDrive/Desktop/gympt/gympt-gitops

# 변경사항 커밋
git add charts/agent-service/values-prod.yaml
git commit -m "feat: Connect Bedrock Agent to agent-service

- Add BEDROCK_AGENT_ID environment variable
- Add BEDROCK_AGENT_ALIAS_ID environment variable
- Add BEDROCK_KNOWLEDGE_BASE_ID environment variable
- Disable mock mode for production"

git push origin main
```

ArgoCD가 자동으로 변경사항을 감지하고 배포합니다.

수동 동기화 (필요시):
```bash
# ArgoCD CLI 사용
argocd app sync agent-service

# 또는 UI에서 Sync 버튼 클릭
# https://argocd.g2mpt.com
```

---

## 4. 배포 확인

### 4.1 Pod 재시작 확인
```bash
kubectl get pods -n gympt-prod -l app.kubernetes.io/name=agent-service

# Pod logs 확인
kubectl logs -n gympt-prod -l app.kubernetes.io/name=agent-service --tail=50
```

**확인 포인트:**
- `ENABLE_BEDROCK_MOCK: false` 로그
- `BEDROCK_AGENT_ID: ABC...` 로그
- Bedrock 클라이언트 초기화 성공 로그
- IAM 권한 오류 없음

### 4.2 Health Check
```bash
# Agent Service Health
curl -X GET https://agent.g2mpt.com/health

# 예상 응답:
# {
#   "status": "healthy",
#   "bedrock": {
#     "enabled": true,
#     "agent_id": "ABCD1234EF",
#     "region": "us-west-2"
#   }
# }
```

---

## 5. 기능 테스트

### 5.1 운동 추천 API 테스트
```bash
curl -X POST https://api.g2mpt.com/api/v1/agent/workout-recommendation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "userId": "test-user-001",
    "goal": "MUSCLE_GAIN",
    "fitnessLevel": "INTERMEDIATE",
    "daysPerWeek": 4,
    "equipmentAvailable": ["BARBELL", "DUMBBELL", "BENCH"]
  }'
```

**검증 사항:**
- 응답 시간 < 10초
- Knowledge Base 인용 포함 (citations)
- 구체적인 운동 계획 (세트/횟수)
- 안전 주의사항 포함

### 5.2 자세 피드백 API 테스트
```bash
curl -X POST https://api.g2mpt.com/api/v1/agent/posture-feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "sessionId": "sess-001",
    "exerciseName": "squat",
    "postureData": {
      "kneeAngle": 85,
      "hipAngle": 90,
      "backAngle": 45,
      "depth": "parallel"
    },
    "repCount": 5
  }'
```

**검증 사항:**
- 실시간 피드백 (< 3초)
- 자세 점수 (0-100)
- 구체적인 개선 사항
- 격려 메시지

### 5.3 Frontend 통합 테스트
1. https://g2mpt.com 접속
2. 로그인 → 대시보드
3. "운동 시작하기" 클릭
4. 운동 추천 받기
5. 자세 분석 진행
6. 리포트 생성 확인

---

## 6. 모니터링 설정

### 6.1 CloudWatch Logs 확인
```bash
# Agent Service 로그
aws logs tail /aws/eks/gympt-prod/agent-service --follow

# Bedrock 호출 로그
aws logs filter-pattern "bedrock" /aws/eks/gympt-prod/agent-service
```

### 6.2 메트릭 확인
- Prometheus: `https://prometheus.g2mpt.com`
- Grafana: `https://grafana.g2mpt.com`

주요 메트릭:
- `agent_interactions_total{interaction_type="workout_recommend"}`
- `agent_interaction_duration_seconds`
- `cache_hits_total{endpoint="workout_recommend"}`
- `bedrock_api_calls_total`
- `bedrock_api_latency_seconds`

### 6.3 알람 설정
CloudWatch Alarms:
- Bedrock API 에러율 > 5%
- Agent 응답 시간 > 10초
- Knowledge Base 검색 실패

---

## 7. 비용 최적화

### 7.1 Bedrock 비용 모니터링
```bash
# 이번 달 Bedrock 사용량
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://bedrock-filter.json
```

### 7.2 캐싱 전략
Agent Service에서 Redis 캐싱 활성화:
- 동일 요청 1시간 캐싱
- 사용자별 프로필 캐싱
- 운동 계획 24시간 캐싱

### 7.3 Rate Limiting
- 사용자당 분당 30회 제한
- Bedrock API 호출 제한 (throttling)

---

## 8. Rollback 계획

문제 발생 시 즉시 롤백:

### 8.1 Mock 모드로 전환
```bash
# values-prod.yaml 수정
# ENABLE_BEDROCK_MOCK: "true"

cd /mnt/c/Users/gandd/OneDrive/Desktop/gympt/gympt-gitops
git add charts/agent-service/values-prod.yaml
git commit -m "rollback: Enable Bedrock mock mode"
git push origin main

# ArgoCD 동기화
argocd app sync agent-service
```

### 8.2 이전 이미지로 롤백
```bash
kubectl rollout undo deployment/agent-service -n gympt-prod

# 특정 버전으로
kubectl rollout undo deployment/agent-service -n gympt-prod --to-revision=11
```

---

## 9. 다음 단계 (추후 개선)

1. **Action Groups 추가**
   - Lambda 함수로 외부 API 호출
   - 사용자 프로필 실시간 조회
   - 운동 세션 자동 저장

2. **Multi-Agent 패턴**
   - Workout Agent: 운동 계획 전담
   - Nutrition Agent: 영양 상담 전담
   - Recovery Agent: 회복/부상 관리

3. **Model Version 관리**
   - Canary Deployment: 신규 모델 점진적 배포
   - A/B Testing: 모델 성능 비교
   - Fallback: 이전 모델로 자동 전환

4. **Knowledge Base 확장**
   - 사용자 피드백 학습
   - 최신 운동 연구 자동 업데이트
   - 다국어 지원 (영어, 일본어)

---

## 체크리스트 요약

- [ ] 1. OpenSearch Serverless Collection 생성
- [ ] 2. S3에 지식 문서 업로드
- [ ] 3. Knowledge Base 생성 및 동기화
- [ ] 4. Bedrock Agent 생성
- [ ] 5. Agent Alias 생성
- [ ] 6. Terraform IAM 적용
- [ ] 7. Helm values 업데이트 (Agent ID, Alias ID, KB ID)
- [ ] 8. GitOps 커밋 및 푸시
- [ ] 9. ArgoCD 배포 확인
- [ ] 10. Pod 재시작 및 로그 확인
- [ ] 11. Health Check API 테스트
- [ ] 12. 운동 추천 API 테스트
- [ ] 13. 자세 피드백 API 테스트
- [ ] 14. Frontend 통합 테스트
- [ ] 15. CloudWatch 로그 확인
- [ ] 16. Grafana 메트릭 확인
- [ ] 17. 비용 모니터링 설정

---

## 참고 문서

- [BEDROCK_AGENT_PRODUCTION_GUIDE.md](./BEDROCK_AGENT_PRODUCTION_GUIDE.md) - 상세 설정 가이드
- [AWS Bedrock Agent Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Titan Embeddings](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
