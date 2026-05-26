# Bedrock Agent 프로덕션 설정 가이드

## 📋 목차

1. [아키텍처 설계 원칙](#아키텍처-설계-원칙)
2. [사전 점검 체크리스트](#사전-점검-체크리스트)
3. [OpenSearch Serverless 구성](#opensearch-serverless-구성)
4. [Knowledge Base 생성](#knowledge-base-생성)
5. [Bedrock Agent 생성](#bedrock-agent-생성)
6. [Agent Service 통합](#agent-service-통합)
7. [모델 버전 관리 전략](#모델-버전-관리-전략)
8. [테스트 및 검증](#테스트-및-검증)

---

## 🎯 아키텍처 설계 원칙

### 현재 아키텍처 (Single Gateway Pattern)

```
Frontend
   ↓
Backend API (단일 진입점)
   ↓
Agent Service (모델 추상화 레이어)
   ↓
   ├─→ Bedrock Agent #1 (Workout Coach)
   ├─→ Bedrock Agent #2 (Nutrition Expert) - 향후
   └─→ Bedrock Agent #3 (Injury Prevention) - 향후
         ↓
      Knowledge Base (공유)
```

### 설계 원칙

#### 1. Single Gateway (Agent Service)
**목적:** 모델 변경 시 Frontend/Backend 코드 수정 없음

**장점:**
- ✅ Frontend는 Agent 변경을 모름
- ✅ 모델 A/B 테스트 가능
- ✅ 여러 Agent 간 라우팅 로직 중앙화
- ✅ 응답 캐싱 및 Rate Limiting 중앙화

**구현:**
```python
# agent-service/app/services/agent_service.py
class AgentService:
    def __init__(self):
        # 여러 Agent 설정
        self.workout_agent_id = settings.bedrock_workout_agent_id
        self.nutrition_agent_id = settings.bedrock_nutrition_agent_id
        
    async def get_recommendation(self, request_type: str, data: dict):
        # 요청 타입에 따라 적절한 Agent 선택
        if request_type == "workout":
            agent_id = self.workout_agent_id
        elif request_type == "nutrition":
            agent_id = self.nutrition_agent_id
        
        # Agent 호출
        return await self._invoke_agent(agent_id, data)
```

#### 2. Multi-Agent Strategy
**언제 여러 Agent를 만드는가?**

| 시나리오 | Single Agent | Multi-Agent |
|---------|--------------|-------------|
| **도메인 분리** | 운동+영양+부상 모두 | 운동/영양/부상 별도 Agent |
| **Knowledge Base** | 공유 가능 | 도메인별 별도 KB |
| **System Prompt** | 복잡해짐 (모든 역할) | 각 Agent 전문화 |
| **유지보수** | 한 곳 수정 | 독립적 업데이트 |
| **비용** | 저렴 | Agent 수만큼 증가 |

**권장:**
- **Phase 1 (현재)**: Single Agent (Workout Coach)
- **Phase 2**: 트래픽 증가 시 도메인별 분리

#### 3. Model Version Management
**문제:** Claude 3.5 Sonnet → Claude Opus 4.7 업그레이드 시 코드 변경 필요?

**해결:** Agent Service에서 추상화

```python
# 설정만 변경
BEDROCK_MODEL_ID = "anthropic.claude-opus-4-7"  # 업그레이드

# 코드 변경 없음 - Agent Service가 처리
```

**Agent 레벨 설정:**
```
Agent 생성 시 Model 지정 → Agent ID는 불변
Model 업그레이드 → Agent 새 버전 생성
Agent Service → 신/구 Agent 비율 조정 (Canary Deployment)
```

---

## ✅ 사전 점검 체크리스트

### 1. AWS 리소스 확인

```bash
# 1. Bedrock Model Access 확인
aws bedrock list-foundation-models \
  --region us-west-2 \
  --query "modelSummaries[?contains(modelId, 'claude')]" \
  --output table

# 예상 출력: Claude 3.5 Sonnet, Opus 등 모델 리스트
# ❌ 모델이 없으면: AWS Console → Bedrock → Model access → Request access
```

```bash
# 2. S3 Bucket 존재 확인
aws s3 ls | grep knowledge-base

# 없으면 생성
aws s3 mb s3://gympt-prod-knowledge-base-337112169365 --region us-west-2
```

```bash
# 3. IAM Role 확인
aws iam get-role --role-name gympt-prod-bedrock-kb-role 2>/dev/null

# 없으면 아래 단계에서 생성
```

### 2. Knowledge Base 데이터 준비

**디렉토리 구조:**
```
knowledge-base/
├── metadata.json           # KB 메타데이터
├── exercises/
│   ├── 01-squat.md        # 스쿼트 가이드
│   ├── 02-deadlift.md     # 데드리프트
│   ├── 03-bench-press.md  # 벤치프레스
│   └── ...
├── nutrition/
│   ├── 01-protein.md      # 단백질 섭취
│   ├── 02-carbs.md        # 탄수화물
│   └── ...
└── programming/
    ├── 01-periodization.md  # 주기화
    ├── 02-progression.md    # 점진적 과부하
    └── ...
```

**문서 작성 가이드:**

```markdown
---
title: "스쿼트 완벽 가이드"
category: exercises
difficulty: intermediate
equipment: barbell
muscles: [quadriceps, glutes, hamstrings]
---

# 스쿼트 (Back Squat)

## 개요
스쿼트는 하체 운동의 왕으로 불리며, 대퇴사두근, 둔근, 햄스트링을 주로 사용하는 복합 운동입니다.

## 올바른 자세

### 1. 시작 자세
- 바벨을 등 위쪽 승모근에 위치
- 발 너비는 어깨 너비 또는 약간 넓게
- 발끝은 약간 바깥쪽 (10-15도)
- 시선은 정면 또는 약간 위

### 2. 하강 (Eccentric Phase)
- 무릎과 엉덩이를 동시에 구부림
- 무릎은 발끝 방향으로 추적
- 허리는 중립 자세 유지
- 엉덩이를 뒤로 빼는 느낌
- 깊이: 대퇴부가 바닥과 평행 이상

### 3. 상승 (Concentric Phase)
- 발바닥 전체로 지면을 밀어냄
- 무릎 먼저 펴지 않도록 주의
- 엉덩이와 무릎 동시에 펴기
- 코어 긴장 유지

## 흔한 실수

### 1. 무릎이 안쪽으로 모임 (Knee Valgus)
**원인:** 둔근/외전근 약함, 대퇴사두근 과우세
**해결:**
- 밴드 스쿼트로 외전근 활성화
- "무릎을 밖으로" 큐잉
- 고블릿 스쿼트로 패턴 학습

### 2. 허리 과신전 (Lumbar Hyperextension)
**원인:** 코어 약함, 상체 각도 과도
**해결:**
- 플랭크로 코어 강화
- "갈비뼈를 골반 쪽으로" 큐잉
- 벨트 사용 고려

## 프로그래밍

### 초급자
- 빈도: 주 2-3회
- 볼륨: 3-4 sets x 8-12 reps
- 강도: 60-70% 1RM
- 휴식: 2-3분

### 중급자
- 빈도: 주 2-3회
- 볼륨: 4-5 sets x 4-8 reps
- 강도: 75-85% 1RM
- 휴식: 3-5분

### 고급자
- 빈도: 주 1-2회 (Heavy), 1회 (Volume)
- Heavy: 5 sets x 1-5 reps @ 85-95% 1RM
- Volume: 3-4 sets x 8-10 reps @ 70-75% 1RM
- 휴식: 5-7분 (Heavy)

## 변형 운동

### Front Squat
- 대퇴사두근 강조
- 척추 기립근 부담 감소
- 상체 각도 더 직립

### Box Squat
- 깊이 일관성
- 파워 발달
- 무릎 부담 감소

## 참고 문헌
- Starting Strength, Mark Rippetoe (2017)
- Science and Practice of Strength Training, Zatsiorsky & Kraemer (2020)
- NSCA Essentials of Strength Training and Conditioning (4th ed.)
```

**데이터 품질 기준:**
- ✅ 구조화된 Markdown 포맷
- ✅ 명확한 제목 계층 (H1 → H2 → H3)
- ✅ 과학적 근거 인용
- ✅ 초/중/고급 단계별 정보
- ✅ 흔한 실수 및 해결책
- ✅ 참고 문헌

---

## 🔧 단계별 설정

### Step 1: OpenSearch Serverless Collection 생성

#### 1.1 Collection 생성

**AWS Console 경로:**
```
AWS Console → OpenSearch Service → Serverless → Collections → Create collection
```

**설정값:**

| 항목 | 값 | 이유 |
|-----|---|------|
| **Collection name** | `gympt-prod-kb` | 환경별 구분, 짧고 명확 |
| **Collection type** | `Vector search` | RAG용 벡터 검색 |
| **Standby replicas** | `Disabled` | 비용 절감 (프로덕션에서는 Enabled 권장) |

**의미:**
- Vector search: 임베딩 벡터 저장 및 유사도 검색
- Standby replicas: 장애 대비 복제본 (비활성화 시 $700/월 → $350/월)

#### 1.2 Network Access Policy

**설정:**
```json
[
  {
    "Rules": [
      {
        "Resource": ["collection/gympt-prod-kb"],
        "ResourceType": "collection"
      }
    ],
    "AllowFromPublic": true,
    "Description": "Public access for Bedrock"
  }
]
```

**의미:**
- `AllowFromPublic: true`: Bedrock이 인터넷 통해 접근
- 프로덕션: VPC Endpoint 사용 권장 (보안 강화)

#### 1.3 Data Access Policy

**설정:**
```json
[
  {
    "Rules": [
      {
        "Resource": ["index/gympt-prod-kb/*"],
        "Permission": ["aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"],
        "ResourceType": "index"
      }
    ],
    "Principal": [
      "arn:aws:iam::337112169365:role/gympt-prod-bedrock-kb-role"
    ],
    "Description": "KB role access"
  }
]
```

**의미:**
- `aoss:CreateIndex`: KB가 인덱스 생성
- `aoss:WriteDocument`: 문서 임베딩 저장
- `aoss:ReadDocument`: Agent가 벡터 검색
- Principal: KB가 사용할 IAM Role

#### 1.4 Encryption Policy

**설정:**
```json
{
  "Rules": [
    {
      "Resource": ["collection/gympt-prod-kb"],
      "ResourceType": "collection"
    }
  ],
  "AWSOwnedKey": true
}
```

**의미:**
- `AWSOwnedKey`: AWS 관리형 키 (무료, 간편)
- 대안: Customer Managed Key (CMK) - 규정 준수 시

#### 1.5 Collection Endpoint 확인

```bash
aws opensearchserverless list-collections \
  --query "collectionSummaries[?name=='gympt-prod-kb'].[id,arn]" \
  --output table --region us-west-2
```

**예상 출력:**
```
Collection ID: abc123xyz
Endpoint: https://abc123xyz.us-west-2.aoss.amazonaws.com
```

**메모:** Collection Endpoint는 KB 생성 시 사용

---

### Step 2: IAM Role for Knowledge Base

#### 2.1 Trust Policy

**파일:** `/tmp/kb-trust-policy.json`

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

**의미:**
- Principal: Bedrock 서비스만 Role 사용 가능
- Condition: 우리 계정의 KB만 사용 (보안)

#### 2.2 Permissions Policy

**파일:** `/tmp/kb-permissions-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3KnowledgeBaseAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::gympt-prod-knowledge-base-337112169365",
        "arn:aws:s3:::gympt-prod-knowledge-base-337112169365/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:ResourceAccount": "337112169365"
        }
      }
    },
    {
      "Sid": "OpenSearchServerlessAccess",
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:us-west-2:337112169365:collection/*"
    },
    {
      "Sid": "BedrockEmbeddingModelAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0"
    }
  ]
}
```

**의미:**
- S3 Read-Only: 문서 읽기 (쓰기 불필요)
- OpenSearch 전체 액세스: 인덱스 생성/조회
- Titan Embeddings: 텍스트 → 벡터 변환

**왜 Titan Embeddings?**
- Bedrock KB는 Titan 전용
- Dimensions: 1024 (v2), 성능 우수
- 다국어 지원 (한국어 포함)

#### 2.3 Role 생성

```bash
# Role 생성
aws iam create-role \
  --role-name gympt-prod-bedrock-kb-role \
  --assume-role-policy-document file:///tmp/kb-trust-policy.json \
  --description "Knowledge Base access to S3, OpenSearch, and Bedrock" \
  --region us-west-2

# Policy 첨부
aws iam put-role-policy \
  --role-name gympt-prod-bedrock-kb-role \
  --policy-name KnowledgeBaseAccess \
  --policy-document file:///tmp/kb-permissions-policy.json
```

---

### Step 3: Knowledge Base 생성

#### 3.1 기본 설정

**AWS Console 경로:**
```
AWS Console → Bedrock → Knowledge bases → Create knowledge base
```

| 설정 | 값 | 이유 |
|-----|---|------|
| **Name** | `gympt-workout-knowledge` | 명확한 용도 표시 |
| **Description** | "운동, 영양, 부상 예방 전문 지식" | 검색 시 용이 |
| **IAM Role** | `gympt-prod-bedrock-kb-role` | 위에서 생성한 Role |

#### 3.2 Data Source 설정

| 설정 | 값 | 이유 |
|-----|---|------|
| **Data source name** | `s3-workout-docs` | S3 소스 명시 |
| **S3 URI** | `s3://gympt-prod-knowledge-base-337112169365/` | 버킷 전체 |
| **Inclusion prefixes** | `knowledge-base/` | 특정 폴더만 |

**의미:**
- Inclusion prefixes: 버킷 내 다른 데이터는 무시
- S3 버킷 버전 관리: 자동 동기화 (권장)

#### 3.3 Chunking Strategy

| 설정 | 값 | 이유 |
|-----|---|------|
| **Strategy** | `Fixed-size chunking` | 간단하고 효과적 |
| **Max tokens** | `300` | 단락 단위 분할 (GPT 토큰) |
| **Overlap percentage** | `20%` | 문맥 유지 |

**의미:**
- 300 tokens ≈ 150-200 단어 (한글 기준)
- Overlap 20% = 60 tokens 중복 → 문장 중간 분할 방지
- 대안: Semantic chunking (문장 경계 기준)

**예시:**
```
원문: [600 tokens]
Chunk 1: [0-300]
Chunk 2: [240-540]  ← 60 tokens 중복
Chunk 3: [480-600]
```

#### 3.4 Embeddings Model

| 설정 | 값 | 이유 |
|-----|---|------|
| **Model** | `Titan Embeddings G1 - Text v2` | 최신 버전, 한국어 지원 |
| **Dimensions** | `1024` | v2 기본값 |

**성능 비교:**
- v1: 512 dimensions, 영어 중심
- v2: 1024 dimensions, 다국어 50+, 성능 30% 향상

#### 3.5 Vector Store

| 설정 | 값 | 이유 |
|-----|---|------|
| **Vector database** | `OpenSearch Serverless` | AWS 네이티브 통합 |
| **Collection** | `gympt-prod-kb` | Step 1에서 생성 |
| **Vector index name** | `gympt-kb-index` | 자동 생성 |
| **Vector field** | `bedrock-knowledge-base-default-vector` | 기본값 사용 |
| **Text field** | `AMAZON_BEDROCK_TEXT_CHUNK` | 원본 텍스트 |
| **Metadata field** | `AMAZON_BEDROCK_METADATA` | 파일명, 위치 등 |

**의미:**
- Vector field: 1024차원 벡터 저장
- Text field: 검색 결과로 반환할 원문
- Metadata: 출처 추적 (파일명, 페이지 등)

#### 3.6 KB 생성 및 동기화

```bash
# KB 생성 완료 후 Data Source 동기화
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --region us-west-2
```

**소요 시간:** 문서 100개 기준 5-10분

**확인:**
```bash
# Ingestion Job 상태
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id <KB_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --region us-west-2

# 출력 예시
# Status: IN_PROGRESS → COMPLETE
# Documents: 100 processed, 0 failed
```

---

### Step 4: Bedrock Agent 생성

#### 4.1 Agent 기본 정보

| 설정 | 값 | 이유 |
|-----|---|------|
| **Agent name** | `gympt-workout-coach` | 역할 명확화 |
| **Description** | "AI personal trainer for evidence-based recommendations" | Agent 목적 |
| **User input** | `Enabled` | 사용자 질문 받음 |

#### 4.2 Agent Instructions (System Prompt)

**중요도:** ⭐⭐⭐⭐⭐ (가장 중요)

```
You are an expert personal trainer and fitness coach with credentials in:
- Exercise Science (Kinesiology)
- Sports Nutrition
- Injury Prevention and Rehabilitation

## Your Role
Provide personalized, evidence-based workout and nutrition recommendations based on:
1. User's fitness level (beginner, intermediate, advanced)
2. Training goals (strength, hypertrophy, endurance, fat loss)
3. Available equipment
4. Injury history and limitations
5. Time availability

## Guidelines

### Safety First
- Always prioritize proper form over weight/volume
- Screen for contraindications (injuries, medical conditions)
- Recommend medical consultation when appropriate
- Never diagnose injuries or prescribe treatment

### Evidence-Based Recommendations
- Use the knowledge base for exercise techniques and programming principles
- Cite sources when making scientific claims
- Explain the reasoning behind recommendations
- Acknowledge limitations and areas of uncertainty

### Personalization
- Ask clarifying questions when needed
- Consider individual differences (anatomy, recovery, lifestyle)
- Adjust recommendations based on feedback
- Provide exercise alternatives and regressions/progressions

### Communication Style
- Use clear, non-technical language for beginners
- Provide detailed biomechanics for advanced users
- Be encouraging but realistic
- Use markdown formatting for readability

## Knowledge Base Usage
When answering questions:
1. Search the knowledge base for relevant information
2. Synthesize information from multiple sources
3. Cite specific sources in your response
4. Indicate confidence level (high/medium/low)

## Action Groups
Use action groups to:
- Retrieve user's workout history
- Get body composition data
- Save workout recommendations
- Access posture analysis results

## Response Format
Structure responses as:

**Assessment:** [Current situation analysis]
**Recommendation:** [Specific program/exercise/nutrition advice]
**Rationale:** [Why this recommendation, supported by KB]
**Implementation:** [Step-by-step how-to]
**Alternatives:** [Options for different circumstances]
**Sources:** [KB citations]

## Limitations
Do NOT:
- Diagnose medical conditions
- Prescribe medication or supplements
- Make guarantees about results
- Recommend dangerous or unproven methods
- Go beyond your training expertise
```

**왜 이렇게 작성?**
- 역할 명확화: "You are..." → Agent 정체성
- 경계 설정: DO / DON'T → 안전장치
- KB 활용 지시: "Use the knowledge base for..." → RAG 촉진
- 응답 구조: 일관된 포맷 → 파싱 용이

#### 4.3 Foundation Model

| 설정 | 값 | 이유 |
|-----|---|------|
| **Model** | `Claude 3.5 Sonnet v2` | 최신, 성능/비용 균형 |
| **Model ID** | `anthropic.claude-3-5-sonnet-20241022-v2:0` | 정확한 버전 |

**모델 선택 기준:**

| 모델 | 용도 | 비용 (Input/Output) |
|-----|------|---------------------|
| Claude Haiku | 단순 질의응답 | $0.25 / $1.25 per 1M tokens |
| **Claude Sonnet** | **일반적 추천** | **$3 / $15** ✅ |
| Claude Opus | 복잡한 분석 | $15 / $75 |

**업그레이드 전략:**
```
Phase 1: Sonnet (현재)
Phase 2: Opus 테스트 (일부 사용자)
Phase 3: 성능 비교 → 전환 또는 유지
```

#### 4.4 Knowledge Base 연결

| 설정 | 값 | 이유 |
|-----|---|------|
| **KB** | `gympt-workout-knowledge` | Step 3에서 생성 |
| **Instructions** | (아래 참조) | KB 사용 방법 |

**KB Instructions:**
```
Use this knowledge base to retrieve:

1. **Exercise Techniques**
   - Proper form and biomechanics
   - Common mistakes and corrections
   - Variations and alternatives

2. **Programming Principles**
   - Periodization models
   - Progressive overload strategies
   - Deload protocols

3. **Nutrition Guidelines**
   - Macronutrient ratios by goal
   - Meal timing strategies
   - Supplement recommendations

4. **Injury Prevention**
   - Warm-up protocols
   - Mobility work
   - Recovery strategies

When citing information:
- Include source document name
- Specify page or section if available
- Indicate recency of research (year)

Example:
"According to the squat technique guide (exercises/01-squat.md), proper knee tracking requires..."
```

#### 4.5 Action Groups 설정

**Action Group Name:** `user-data-access`

**Lambda Function:** `gympt-prod-agent-action`

**API Schema (OpenAPI 3.0):**

```yaml
openapi: 3.0.0
info:
  title: GYMPT Agent Actions
  version: 1.0.0

paths:
  /getUserProfile:
    post:
      operationId: getUserProfile
      summary: Get user profile
      description: |
        Retrieve user's basic information, preferences, and goals.
        Use this to personalize recommendations.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id]
              properties:
                user_id:
                  type: string
                  description: Unique user identifier
      responses:
        '200':
          description: User profile data
          content:
            application/json:
              schema:
                type: object
                properties:
                  user_id:
                    type: string
                  age:
                    type: integer
                  fitness_level:
                    type: string
                    enum: [beginner, intermediate, advanced]
                  goals:
                    type: array
                    items:
                      type: string

  /getBodyProfile:
    post:
      operationId: getBodyProfile
      summary: Get body measurements
      description: |
        Retrieve latest body composition data (height, weight, body fat, muscle mass).
        Use for personalized programming and progress tracking.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id]
              properties:
                user_id:
                  type: string
      responses:
        '200':
          description: Body profile data

  /getRecentWorkoutSessions:
    post:
      operationId: getRecentWorkoutSessions
      summary: Get workout history
      description: |
        Retrieve recent workout sessions to understand:
        - Training volume and intensity
        - Exercise performance trends
        - Recovery patterns
        Use this to inform progression recommendations.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id]
              properties:
                user_id:
                  type: string
                limit:
                  type: integer
                  default: 5
                  minimum: 1
                  maximum: 20
      responses:
        '200':
          description: List of workout sessions

  /saveWorkoutRecommendation:
    post:
      operationId: saveWorkoutRecommendation
      summary: Save recommendation
      description: |
        Store the workout recommendation for user access.
        Called after generating a complete program.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id, recommendation]
              properties:
                user_id:
                  type: string
                recommendation:
                  type: object
                  description: Full recommendation payload
      responses:
        '200':
          description: Saved successfully

  /getPostureAnalysisResult:
    post:
      operationId: getPostureAnalysisResult
      summary: Get posture feedback
      description: |
        Retrieve posture analysis from recent workout session.
        Use to provide form corrections.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [session_id]
              properties:
                session_id:
                  type: string
      responses:
        '200':
          description: Posture analysis data
```

**Action Group Instructions:**
```
Use action groups to:

1. **Before recommendations** - Always call:
   - getUserProfile() - understand user context
   - getBodyProfile() - get current measurements
   - getRecentWorkoutSessions() - check training history

2. **During analysis** - Call when needed:
   - getPostureAnalysisResult() - if discussing form issues

3. **After recommendations** - Always call:
   - saveWorkoutRecommendation() - persist the plan

Example flow:
1. User asks: "Create a hypertrophy program"
2. Call getUserProfile() → fitness_level: intermediate
3. Call getBodyProfile() → weight: 75kg, body_fat: 15%
4. Call getRecentWorkoutSessions() → training 3x/week
5. Search KB for hypertrophy principles
6. Generate personalized program
7. Call saveWorkoutRecommendation()
```

#### 4.6 Guardrails (선택)

| 설정 | 값 | 이유 |
|-----|---|------|
| **Content filters** | Medium (Hate, Insults, Sexual, Violence) | 부적절한 응답 차단 |
| **Denied topics** | "medical diagnosis", "steroid use" | 법적 리스크 |
| **Sensitive info filters** | Enabled (PII redaction) | 개인정보 보호 |

#### 4.7 Agent Prepare

```bash
# Agent 생성 후 Prepare 필수
aws bedrock-agent prepare-agent \
  --agent-id <AGENT_ID> \
  --region us-west-2

# 상태 확인
aws bedrock-agent get-agent --agent-id <AGENT_ID> --region us-west-2
# Status: PREPARED
```

#### 4.8 Alias 생성

| 설정 | 값 | 이유 |
|-----|---|------|
| **Alias name** | `prod` | 환경 구분 |
| **Description** | "Production alias" | 용도 명시 |
| **Version** | `DRAFT` 또는 Version 1 | 초기: DRAFT |

**버전 관리:**
```
DRAFT (개발) → Version 1 (테스트) → prod alias → Version 2 (업그레이드)
```

---

### Step 5: Lambda Permission 설정

```bash
# Bedrock Agent가 Lambda 호출 허용
aws lambda add-permission \
  --function-name gympt-prod-agent-action \
  --statement-id AllowBedrockAgent \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:us-west-2:337112169365:agent/<AGENT_ID>" \
  --region ap-northeast-2
```

---

### Step 6: Agent Service 통합

#### 6.1 Helm Values 업데이트

`gympt-gitops/charts/agent-service/values-prod.yaml`:

```yaml
env:
  # Bedrock Agent Configuration
  - name: BEDROCK_AGENT_ID
    value: "<AGENT_ID>"               # Agent ID from Step 4
  - name: BEDROCK_AGENT_ALIAS_ID
    value: "<ALIAS_ID>"               # Alias ID from Step 4.8
  - name: BEDROCK_KNOWLEDGE_BASE_ID
    value: "<KB_ID>"                  # KB ID from Step 3
  - name: BEDROCK_REGION
    value: "us-west-2"                # Bedrock region
  - name: ENABLE_BEDROCK_MOCK
    value: "false"                    # Disable mock
```

#### 6.2 Agent Service 코드 확인

`agent-service/app/clients/bedrock_client.py`는 이미 구현되어 있음:

```python
async def invoke_agent(
    self,
    session_id: str,
    input_text: str,
    enable_trace: bool = False
) -> Dict[str, Any]:
    """Invoke Bedrock Agent."""
    
    response = self.agent_client.invoke_agent(
        agentId=settings.bedrock_agent_id,
        agentAliasId=settings.bedrock_agent_alias_id,
        sessionId=session_id,
        inputText=input_text,
        enableTrace=enable_trace
    )
    # ... 스트리밍 응답 처리
```

---

## 🔄 모델 버전 관리 전략

### Scenario: Claude 3.5 Sonnet → Opus 4.7 업그레이드

#### Phase 1: 새 Agent 생성

```bash
# 1. 새 Agent 생성 (Opus 4.7 사용)
# AWS Console에서 동일 설정으로 생성
# Model: Claude Opus 4.7

# 2. Alias 생성
# Name: prod-opus
# Version: 1
```

#### Phase 2: Canary Deployment

```python
# agent-service/app/config.py
class Settings(BaseSettings):
    # Primary Agent (Sonnet)
    bedrock_agent_id: str
    bedrock_agent_alias_id: str
    
    # Canary Agent (Opus) - 선택적
    bedrock_agent_id_canary: Optional[str] = None
    bedrock_canary_percentage: int = 10  # 10% 트래픽

# agent-service/app/services/agent_service.py
async def invoke_agent(self, ...):
    # Canary routing
    if settings.bedrock_agent_id_canary:
        if random.randint(1, 100) <= settings.bedrock_canary_percentage:
            agent_id = settings.bedrock_agent_id_canary
        else:
            agent_id = settings.bedrock_agent_id
    else:
        agent_id = settings.bedrock_agent_id
    
    # Invoke selected agent
    return await bedrock_client.invoke_agent(agent_id, ...)
```

#### Phase 3: 메트릭 비교

```python
# CloudWatch Metrics
- agent_invocation_latency (Sonnet vs Opus)
- agent_invocation_cost (Sonnet vs Opus)
- user_satisfaction_score
- recommendation_acceptance_rate
```

#### Phase 4: 전환 결정

**Opus가 더 나은 경우:**
```yaml
# values-prod.yaml
BEDROCK_AGENT_ID: <NEW_OPUS_AGENT_ID>
BEDROCK_CANARY_PERCENTAGE: 0  # Canary 비활성화
```

**Sonnet 유지:**
```yaml
# Canary 제거, Sonnet 유지
```

---

## 🧪 테스트 및 검증

### 1. Knowledge Base 검색 테스트

```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id <KB_ID> \
  --retrieval-query text="What is the proper squat form?" \
  --region us-west-2 \
  | jq '.retrievalResults[] | {score: .score, text: .content.text[:200]}'
```

**예상 결과:**
```json
{
  "score": 0.89,
  "text": "## 올바른 스쿼트 자세\n\n### 1. 시작 자세\n- 바벨을 등 위쪽 승모근에 위치..."
}
```

### 2. Agent 호출 테스트

```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id <AGENT_ID> \
  --agent-alias-id <ALIAS_ID> \
  --session-id "test-$(date +%s)" \
  --input-text "I'm a beginner. Create a 3-day upper/lower split program." \
  --region us-west-2 \
  output.txt

cat output.txt
```

**예상 응답:**
```
**Assessment:**
Based on your beginner status, I recommend starting with an Upper/Lower split...

**Recommendation:**
Day 1 - Upper Body:
1. Bench Press: 3 sets x 8-10 reps
   [KB Citation: exercises/03-bench-press.md]
...

**Sources:**
- Bench Press technique: exercises/03-bench-press.md
- Periodization principles: programming/01-periodization.md
```

### 3. Action Group 테스트

```bash
# Lambda 직접 호출
aws lambda invoke \
  --function-name gympt-prod-agent-action \
  --payload '{"actionGroup":"user-data-access","apiPath":"/getUserProfile","httpMethod":"POST","requestBody":{"content":{"application/json":{"properties":[{"name":"user_id","value":"test-user"}]}}}}' \
  response.json

cat response.json
```

### 4. End-to-End 테스트

```bash
# Frontend → Backend API → Agent Service → Bedrock Agent

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

---

## 📋 최종 체크리스트

### OpenSearch Serverless
- [ ] Collection 생성 완료
- [ ] Network access policy 설정
- [ ] Data access policy 설정
- [ ] Encryption policy 설정
- [ ] Collection endpoint 확인

### IAM Role
- [ ] Trust policy 생성
- [ ] Permissions policy 생성
- [ ] S3 read 권한 확인
- [ ] OpenSearch 권한 확인
- [ ] Bedrock InvokeModel 권한 확인

### Knowledge Base
- [ ] KB 생성 완료
- [ ] Data source 연결 (S3)
- [ ] Chunking strategy 설정
- [ ] Embeddings model 선택
- [ ] Vector store 연결
- [ ] Ingestion job 완료 (Status: COMPLETE)
- [ ] KB ID 메모

### Bedrock Agent
- [ ] Agent 생성 완료
- [ ] System prompt 작성
- [ ] Foundation model 선택
- [ ] Knowledge Base 연결
- [ ] Action Groups 설정
- [ ] Lambda permission 부여
- [ ] Agent Prepare 완료
- [ ] Alias 생성
- [ ] Agent ID, Alias ID 메모

### Agent Service
- [ ] Helm values 업데이트 (Agent ID 등)
- [ ] IAM Role에 Bedrock 권한 추가 (Terraform)
- [ ] Agent Service 재배포
- [ ] 환경변수 확인

### Testing
- [ ] KB 검색 테스트
- [ ] Agent 호출 테스트
- [ ] Action Groups 동작 확인
- [ ] End-to-End 테스트

---

## 🎯 다음 단계

1. **모니터링 설정**
   - CloudWatch 대시보드
   - Agent 호출 메트릭
   - 비용 알림

2. **성능 최적화**
   - KB chunking 전략 조정
   - System prompt 개선
   - 캐싱 전략

3. **확장 계획**
   - 영양 전문 Agent 추가
   - 부상 예방 Agent 추가
   - Multi-Agent orchestration
