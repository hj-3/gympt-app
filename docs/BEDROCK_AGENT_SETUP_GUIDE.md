# Bedrock Agent + Knowledge Base 설정 가이드

## 📋 개요

**프로젝트 목적:**
- ✅ **Bedrock Agent 사용** (필수)
- ✅ **Knowledge Base (RAG)** 연동 (필수)
- ✅ **운동 관련 전문 지식** 기반으로 근거 있는 추천
- ✅ **Action Groups**를 통한 외부 시스템 연동

**아키텍처:**
```
Frontend → Backend API → Agent Service → Bedrock Agent
                                              ↓
                                         Knowledge Base (RAG)
                                              ↓
                                         OpenSearch Serverless
                                              ↓
                                         Action Groups (Lambda)
```

---

## 🏗️ 전체 구성 요소

### 1. Knowledge Base (운동 지식 저장소)
- **목적**: 운동 매뉴얼, 영양 가이드, 부상 예방법 등 전문 지식 제공
- **데이터 소스**: S3 (Markdown, PDF 문서)
- **벡터 DB**: OpenSearch Serverless
- **임베딩 모델**: Amazon Titan Embeddings

### 2. Bedrock Agent
- **목적**: 사용자 질문 → KB 검색 → 컨텍스트 기반 답변
- **Foundation Model**: Claude 3.5 Sonnet
- **Guardrails**: 안전장치 (선택)

### 3. Action Groups
- **Lambda Functions**: 외부 시스템 호출 (운동 기록 조회, 추천 저장 등)
- **연결**: `gympt-prod-agent-action` Lambda

---

## 📦 사전 준비 사항

### 1. S3 Bucket (Knowledge Base 데이터)

이미 생성되어 있습니다:
```bash
# 확인
aws s3 ls | grep knowledge
```

없으면 생성:
```bash
aws s3 mb s3://gympt-prod-knowledge-base-337112169365 --region us-west-2
```

### 2. 운동 지식 문서 준비

**디렉토리 구조:**
```
knowledge-base/
├── exercise-library/
│   ├── upper-body.md
│   ├── lower-body.md
│   ├── core.md
│   └── cardio.md
├── nutrition/
│   ├── macro-basics.md
│   ├── meal-timing.md
│   └── supplements.md
├── injury-prevention/
│   ├── warmup-protocols.md
│   ├── mobility.md
│   └── recovery.md
└── programming/
    ├── periodization.md
    ├── progression-models.md
    └── deload-strategy.md
```

**문서 포맷 (Markdown 권장):**
```markdown
# Upper Body Exercises

## Bench Press

**목적**: 가슴, 어깨, 삼두근 발달

**수행 방법:**
1. 벤치에 누워 발을 바닥에 고정
2. 바를 어깨 너비보다 약간 넓게 잡기
3. 가슴까지 천천히 내리기
4. 폭발적으로 밀어올리기

**주의사항:**
- 허리를 과도하게 들지 않기
- 팔꿈치를 45도 각도 유지
- 완전한 가동범위 사용

**프로그래밍:**
- 초급: 3 sets x 8-10 reps
- 중급: 4 sets x 6-8 reps
- 고급: 5 sets x 4-6 reps

**참고 자료:**
- Starting Strength, Mark Rippetoe
- Science and Practice of Strength Training, Zatsiorsky
```

### 3. S3에 문서 업로드

```bash
# 로컬에서 S3로 업로드
aws s3 sync ./knowledge-base/ s3://gympt-prod-knowledge-base-337112169365/knowledge-base/ \
  --region us-west-2
```

---

## 🔧 Step 1: OpenSearch Serverless Collection 생성

### 1.1 AWS Console에서 생성

**경로:** AWS Console → OpenSearch Service → Serverless collections

**설정:**
- **Collection name**: `gympt-knowledge-base`
- **Collection type**: Vector search
- **Encryption**: AWS owned key
- **Network**: Public access (또는 VPC)
- **Data access policy**:
  ```json
  {
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/gympt-knowledge-base/*"],
        "Permission": ["aoss:*"]
      }
    ],
    "Principal": [
      "arn:aws:iam::337112169365:role/gympt-prod-bedrock-kb-role"
    ]
  }
  ```

### 1.2 Collection Endpoint 확인

```bash
aws opensearchserverless list-collections \
  --query "collectionSummaries[?name=='gympt-knowledge-base'].id" \
  --output text
```

Endpoint 형식:
```
https://xxxxxx.us-west-2.aoss.amazonaws.com
```

---

## 🔧 Step 2: IAM Role for Knowledge Base

### 2.1 Trust Policy

**Role name**: `gympt-prod-bedrock-kb-role`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "337112169365"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:us-west-2:337112169365:knowledge-base/*"
        }
      }
    }
  ]
}
```

### 2.2 Permissions Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::gympt-prod-knowledge-base-337112169365",
        "arn:aws:s3:::gympt-prod-knowledge-base-337112169365/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:us-west-2:337112169365:collection/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1"
    }
  ]
}
```

### 2.3 AWS CLI로 생성

```bash
# Trust policy 파일 생성
cat > /tmp/kb-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "bedrock.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Role 생성
aws iam create-role \
  --role-name gympt-prod-bedrock-kb-role \
  --assume-role-policy-document file:///tmp/kb-trust-policy.json \
  --region us-west-2

# Permissions policy 첨부
aws iam put-role-policy \
  --role-name gympt-prod-bedrock-kb-role \
  --policy-name KnowledgeBaseAccess \
  --policy-document file:///tmp/kb-permissions-policy.json
```

---

## 🔧 Step 3: Knowledge Base 생성

### 3.1 AWS Console 설정

**경로:** AWS Console → Bedrock → Knowledge bases → Create knowledge base

#### 기본 정보
- **Name**: `gympt-workout-knowledge`
- **Description**: 운동, 영양, 부상 예방 관련 전문 지식 베이스
- **IAM Role**: `gympt-prod-bedrock-kb-role`

#### Data source
- **Data source name**: `s3-workout-docs`
- **S3 URI**: `s3://gympt-prod-knowledge-base-337112169365/knowledge-base/`
- **Chunking strategy**: Default chunking
- **Max tokens**: 300
- **Overlap percentage**: 20%

#### Embeddings model
- **Model**: Amazon Titan Embeddings G1 - Text
- **Dimensions**: 1536

#### Vector database
- **Vector database**: OpenSearch Serverless
- **Collection**: `gympt-knowledge-base`
- **Vector index name**: `gympt-kb-index`
- **Vector field**: `vector`
- **Text field**: `text`
- **Metadata field**: `metadata`

### 3.2 Sync Data Source

생성 후 "Sync" 버튼 클릭하여 S3 문서를 인덱싱:
```bash
# CLI로 동기화
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --region us-west-2
```

### 3.3 Knowledge Base ID 확인

```bash
aws bedrock-agent list-knowledge-bases --region us-west-2

# 출력 예시
{
  "knowledgeBaseSummaries": [
    {
      "knowledgeBaseId": "XXXXXXXXXX",
      "name": "gympt-workout-knowledge",
      "status": "ACTIVE"
    }
  ]
}
```

**Knowledge Base ID를 메모하세요**: `XXXXXXXXXX`

---

## 🔧 Step 4: Bedrock Agent 생성

### 4.1 Agent 기본 설정

**경로:** AWS Console → Bedrock → Agents → Create agent

#### Agent details
- **Agent name**: `gympt-fitness-coach`
- **Agent description**: AI personal trainer providing evidence-based workout and nutrition recommendations
- **Agent resource role**: Create and use a new service role
- **Idle session timeout**: 10 minutes

#### Foundation model
- **Model**: Claude 3.5 Sonnet v2
- **Model ID**: `anthropic.claude-3-5-sonnet-20241022-v2:0`

#### Instructions (System Prompt)
```
You are an expert personal trainer and fitness coach with deep knowledge of:
- Exercise science and biomechanics
- Program design and periodization
- Nutrition for performance and body composition
- Injury prevention and rehabilitation
- Evidence-based training methods

Your role is to:
1. Provide personalized workout recommendations based on user's goals, fitness level, and available equipment
2. Answer questions about exercise technique, programming, and nutrition
3. Use the knowledge base to provide accurate, evidence-based information
4. Cite sources from the knowledge base when making recommendations
5. Adjust recommendations based on user's training history and feedback

Guidelines:
- Always prioritize safety and proper form
- Consider individual limitations (injuries, equipment, time)
- Provide progressive overload strategies
- Explain the reasoning behind recommendations
- Use clear, actionable language
- Ask clarifying questions when needed

When recommending workouts:
- Specify sets, reps, and rest periods
- Include warm-up and cool-down
- Provide exercise alternatives when needed
- Consider recovery and training frequency

Format responses:
- Use markdown formatting
- Break down complex information
- Provide step-by-step instructions
- Include relevant metrics (RPE, %1RM, etc.)
```

### 4.2 Knowledge Base 연결

**Add knowledge base:**
- Select: `gympt-workout-knowledge`
- Instructions for KB use:
  ```
  Use this knowledge base to retrieve information about:
  - Exercise techniques and variations
  - Programming principles (periodization, progression)
  - Nutrition guidelines (macros, timing, supplements)
  - Injury prevention and recovery protocols
  
  Always cite specific information from the knowledge base.
  Prioritize evidence-based recommendations over general advice.
  ```

### 4.3 Action Groups 설정

**Add action group:**

#### Action group details
- **Action group name**: `user-data-actions`
- **Action group type**: Define with API schemas
- **Description**: Access user workout history, body measurements, and save recommendations

#### Lambda function
- **Select Lambda**: `gympt-prod-agent-action`
- **Prepare function**: Manually configure

#### API Schema (OpenAPI 3.0)

```yaml
openapi: 3.0.0
info:
  title: GYMPT Agent Actions API
  version: 1.0.0
  description: Action group for accessing user data and saving recommendations

paths:
  /getUserProfile:
    post:
      summary: Get user profile information
      description: Retrieve user's basic profile, preferences, and goals
      operationId: getUserProfile
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                  description: User identifier
      responses:
        '200':
          description: User profile data
          content:
            application/json:
              schema:
                type: object

  /getBodyProfile:
    post:
      summary: Get latest body measurements
      description: Retrieve user's most recent body composition data
      operationId: getBodyProfile
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
      responses:
        '200':
          description: Body profile data

  /getRecentWorkoutSessions:
    post:
      summary: Get recent workout history
      description: Retrieve user's recent workout sessions for analysis
      operationId: getRecentWorkoutSessions
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                limit:
                  type: integer
                  default: 5
      responses:
        '200':
          description: List of recent workout sessions

  /saveWorkoutRecommendation:
    post:
      summary: Save workout recommendation
      description: Store AI-generated workout recommendation for user
      operationId: saveWorkoutRecommendation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                recommendation:
                  type: object
                  description: Workout recommendation details
      responses:
        '200':
          description: Recommendation saved

  /getPostureAnalysisResult:
    post:
      summary: Get posture analysis from recent session
      description: Retrieve posture feedback for exercise form analysis
      operationId: getPostureAnalysisResult
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: string
      responses:
        '200':
          description: Posture analysis data

  /createWorkoutReport:
    post:
      summary: Queue workout report generation
      description: Trigger report generation with AI insights
      operationId: createWorkoutReport
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                session_id:
                  type: string
      responses:
        '200':
          description: Report queued for generation
```

**Instructions for action group:**
```
Use these actions to:
- Retrieve user's workout history before making recommendations
- Get body measurements to personalize programs
- Save recommendations so user can access them later
- Analyze form issues from posture analysis
- Queue report generation after workouts

Always check user's recent history before recommending new exercises.
Consider injury history and limitations from profile.
```

### 4.4 Guardrails (선택)

**Enable guardrails:**
- **Content filters**: Hate, Insults, Sexual, Violence (Medium)
- **Denied topics**: Medical diagnosis, Steroid recommendations
- **Word filters**: 욕설, 부적절한 언어
- **Sensitive information filters**: PII redaction

### 4.5 Create Agent

**Create** 버튼 클릭 후 **Prepare** 실행:
```bash
# CLI로 Prepare
aws bedrock-agent prepare-agent \
  --agent-id <AGENT_ID> \
  --region us-west-2
```

### 4.6 Create Alias

**Create alias:**
- **Alias name**: `prod`
- **Description**: Production alias
- **Associate with version**: DRAFT or specific version

**Alias ID를 메모하세요**: `XXXXXXXXXX`

---

## 🔧 Step 5: Lambda Function 권한 설정

### 5.1 Lambda Resource Policy

Bedrock Agent가 Lambda를 호출할 수 있도록 권한 부여:

```bash
aws lambda add-permission \
  --function-name gympt-prod-agent-action \
  --statement-id AllowBedrockAgentInvoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-west-2:337112169365:agent/<AGENT_ID>" \
  --region ap-northeast-2
```

### 5.2 Lambda 환경변수 추가

```bash
aws lambda update-function-configuration \
  --function-name gympt-prod-agent-action \
  --environment "Variables={
    BEDROCK_AGENT_ID=<AGENT_ID>,
    BEDROCK_AGENT_ALIAS_ID=<ALIAS_ID>,
    DYNAMODB_TABLE_PREFIX=gympt-prod
  }" \
  --region ap-northeast-2
```

---

## 🔧 Step 6: Agent Service 설정 업데이트

### 6.1 Helm Values 업데이트

`gympt-gitops/charts/agent-service/values-prod.yaml`:

```yaml
env:
  - name: APP_ENV
    value: "prod"
  - name: ENABLE_BEDROCK_MOCK
    value: "false"
  - name: BEDROCK_REGION
    value: "us-west-2"
  - name: BEDROCK_MODEL_ID
    value: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  # Bedrock Agent Configuration
  - name: BEDROCK_AGENT_ID
    value: "<AGENT_ID>"
  - name: BEDROCK_AGENT_ALIAS_ID
    value: "<ALIAS_ID>"
  - name: BEDROCK_KNOWLEDGE_BASE_ID
    value: "<KB_ID>"
  # Redis, DynamoDB, etc...
```

### 6.2 Agent Service 코드 확인

`agent-service/app/config.py`가 환경변수를 읽도록 설정되어 있는지 확인:
```python
bedrock_agent_id: Optional[str] = None
bedrock_agent_alias_id: Optional[str] = None
bedrock_knowledge_base_id: Optional[str] = None
```

---

## 🧪 Step 7: 테스트

### 7.1 Knowledge Base 검색 테스트

```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id <KB_ID> \
  --retrieval-query text="What is the proper bench press technique?" \
  --region us-west-2
```

**예상 결과:**
```json
{
  "retrievalResults": [
    {
      "content": {
        "text": "Bench Press Technique: 1. Lie on bench with feet flat..."
      },
      "score": 0.95,
      "location": {
        "s3Location": {
          "uri": "s3://gympt-prod-knowledge-base-337112169365/knowledge-base/exercise-library/upper-body.md"
        }
      }
    }
  ]
}
```

### 7.2 Agent 호출 테스트

```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id <AGENT_ID> \
  --agent-alias-id <ALIAS_ID> \
  --session-id "test-session-$(date +%s)" \
  --input-text "I'm a beginner. Recommend a 3-day per week upper/lower split." \
  --region us-west-2 \
  --output-file /tmp/agent-response.txt

cat /tmp/agent-response.txt
```

**예상 결과:**
```
Based on your beginner status and 3-day per week availability, 
I recommend an Upper/Lower split:

**Day 1 - Upper Body:**
1. Bench Press: 3 sets x 8-10 reps
   - Focus on controlled descent, explosive concentric
   - Rest 2-3 minutes between sets
   
2. Bent-Over Rows: 3 sets x 8-10 reps
   ...

[Knowledge Base Citation: exercise-library/upper-body.md, programming/progression-models.md]
```

### 7.3 End-to-End 테스트

Frontend에서 AI 추천 받기:
1. `/profile/ai-coach` 접속
2. "새로운 추천 받기" 클릭
3. 목표, 운동 수준 입력
4. **실제 Bedrock Agent 응답 확인** (Knowledge Base 인용 포함)

---

## 📊 모니터링 및 디버깅

### Agent Invocation 로그

```bash
# CloudWatch Logs 확인
aws logs tail /aws/bedrock/agents/<AGENT_ID> --follow --region us-west-2
```

### Knowledge Base 검색 성능

```bash
# KB 메트릭
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name RetrievalLatency \
  --dimensions Name=KnowledgeBaseId,Value=<KB_ID> \
  --start-time 2026-05-25T00:00:00Z \
  --end-time 2026-05-26T00:00:00Z \
  --period 3600 \
  --statistics Average \
  --region us-west-2
```

### Agent Service 로그

```bash
kubectl logs -n gympt-prod deployment/agent-service --tail=100 --follow | grep -E "agent|bedrock"
```

---

## 💰 비용 추정

### Knowledge Base
- **OpenSearch Serverless**: ~$700/월 (4 OCU)
- **S3 Storage**: ~$1/월 (10GB)
- **Embeddings**: ~$0.0001/token

### Bedrock Agent
- **Agent 호출**: $0.00025/1K requests
- **Claude 3.5 Sonnet**: Input $3/1M tokens, Output $15/1M tokens
- **KB 검색**: $0.0001/1K tokens

### 월간 예상 (1만 사용자, 월 10만 추천)
- OpenSearch: $700
- Bedrock Agent: $25
- Claude: $200
- KB 검색: $10
- **Total**: ~$935/월

---

## 🔐 보안 고려사항

### 1. IAM Least Privilege
- Agent role은 필요한 리소스만 접근
- Lambda는 Bedrock에서만 호출 가능

### 2. Data Privacy
- Knowledge Base에 개인정보 저장 금지
- Action Group을 통해서만 사용자 데이터 접근

### 3. Guardrails
- 부적절한 응답 차단
- PII 자동 제거
- Medical advice 거부

### 4. Rate Limiting
- Agent Service에서 rate limit 적용
- CloudFront에서도 rate limit 설정

---

## 📝 체크리스트

### Knowledge Base 설정
- [ ] S3 bucket 생성
- [ ] 운동 지식 문서 작성 및 업로드
- [ ] OpenSearch Serverless collection 생성
- [ ] IAM role for KB 생성
- [ ] Knowledge Base 생성 및 동기화
- [ ] KB ID 메모

### Bedrock Agent 설정
- [ ] Agent 생성 (Claude 3.5 Sonnet)
- [ ] System prompt 설정
- [ ] Knowledge Base 연결
- [ ] Action Groups 설정
- [ ] Lambda 권한 부여
- [ ] Alias 생성
- [ ] Agent ID, Alias ID 메모

### Agent Service 연동
- [ ] Helm values에 Agent ID 추가
- [ ] IAM role에 Bedrock Agent 권한 추가
- [ ] Agent Service 재배포
- [ ] 환경변수 확인

### 테스트
- [ ] KB 검색 테스트
- [ ] Agent 호출 테스트
- [ ] Action Groups 동작 확인
- [ ] End-to-End 테스트
- [ ] 응답 품질 검증

---

## 🆘 문제 해결

### Agent가 응답하지 않음
```bash
# Agent 상태 확인
aws bedrock-agent get-agent --agent-id <AGENT_ID> --region us-west-2

# Agent를 Prepare 했는지 확인
# Status가 PREPARED여야 함
```

### Knowledge Base 검색 결과 없음
```bash
# 데이터 소스 동기화 상태 확인
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --region us-west-2

# 실패했으면 재시도
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --region us-west-2
```

### Action Groups Lambda 호출 실패
```bash
# Lambda 권한 확인
aws lambda get-policy --function-name gympt-prod-agent-action

# Bedrock가 Principal로 있는지 확인
```

### OpenSearch Serverless 접근 불가
```bash
# Data access policy 확인
aws opensearchserverless get-access-policy \
  --name gympt-knowledge-base \
  --type data

# Bedrock role이 포함되어 있는지 확인
```

---

## 📚 참고 자료

- [Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Knowledge Bases for Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)

---

## ✅ 다음 단계

이 가이드를 따라 설정 완료 후:

1. **지식 베이스 확장**
   - 더 많은 운동 문서 추가
   - 과학적 연구 논문 추가
   - 영양 가이드 업데이트

2. **Agent 성능 튜닝**
   - System prompt 개선
   - KB 검색 파라미터 조정
   - Chunking 전략 최적화

3. **모니터링 대시보드**
   - CloudWatch 대시보드 생성
   - 응답 품질 메트릭 추적
   - 비용 모니터링

4. **A/B 테스팅**
   - 다른 Foundation Model 테스트
   - System prompt 변형 테스트
   - KB 검색 전략 비교
