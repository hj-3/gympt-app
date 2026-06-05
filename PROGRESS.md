# GYMPT 작업 진행 상황

> 최종 업데이트: 2026-06-06
> 대상 저장소: gympt-app / gympt-infra / gympt-gitops (3개 모두 main 동기화 완료)

---

## 1. Bedrock Agent 통합

AI 퍼스널 트레이너를 직접 모델 호출이 아닌 **Bedrock Agent** 경유로 전환했습니다.

- `bedrock_client.invoke_agent()`에 `sessionState.sessionAttributes` 지원 추가 → user_id·context를 Agent 세션에 전달
- `agent_service.py`의 운동 추천/자세 피드백/리포트 **3개 경로 모두 `invoke_agent()` 사용** (기존엔 일부가 `invoke_model` 직접 호출)
- `src/services/bedrock_agent_service.py`의 `List` import 누락 버그 수정

### Bedrock Agent 콘솔 설정 (운영 반영 완료)
- Agent ID: `WPQ0RESSZS`, prod alias: `E5LE29XZS1`, 모델: Claude Sonnet 4.5 (inference profile)
- **UserInput 액션 그룹(`AMAZON.UserInput`) 비활성화** — 에이전트가 운동 계획을 바로 생성하지 않고 사용자에게 되묻던 문제(+간헐적 무응답/500) 해결
- 시스템 지침에 한국어 강제 응답 + 맨몸운동 목록 제약 + "정보 부족해도 즉시 생성" 규칙 추가

---

## 2. SQS / Lambda 비동기 파이프라인 연동

서비스 → SQS → Lambda 메시지 포맷 불일치를 정리하고, 누락된 트리거를 연결했습니다.

| 큐 | 발행 | 소비 Lambda | 변경 |
|----|------|------------|------|
| posture-event-queue | posture-analysis-service | posture-event-processor | camelCase + `analysis.{score,issues}` 포맷으로 수정 |
| report-generation-queue | agent-service | report-generator | `userId`/`period`/`periodStart·End` 포맷 정렬 |
| recommendation-update-queue | backend-api | recommendation-update | 완료 후 notification 발행 추가 |
| notification-queue | 각 Lambda + backend-api | notification | WORKOUT_COMPLETED / RECOMMENDATION_UPDATE 연결 |

- `report-generator`: `periodStart/End` 직접 사용 + `ENABLE_BEDROCK_MOCK` 기본값 `false`
- `backend-api`: `SqsService.publishWorkoutCompletedNotification()` 추가, `application.yml`에 큐 URL 환경변수 추가

---

## 3. 프론트엔드 버그 수정

- **401 간헐 오류**: `useEffect([], [])`가 Cognito 세션 확립 전 API 호출 → 의존성을 `[user?.userId]`로 변경 (body 최신/이력, ai-coach)
- **폰트 preload 경고**: Inter 폰트 `display: 'swap'` 추가
- **UI 깨짐**: `globals.css` body 그라디언트 배경이 Tailwind `bg-gray-50`과 충돌 → 제거

---

## 4. 회원가입 나이·성별 입력 (DB 저장)

- 회원가입 폼에 나이(숫자)·성별(남/여/기타) 입력란 추가 + 검증
- 이메일 인증 후 자동 로그인 직후 `PUT /api/v1/users/me`로 DB 저장 (비차단)
- 백엔드 `UserProfileRequest`(age/gender)·`updateProfileByCognitoSub`가 이미 지원 → 백엔드 변경 불필요

---

## 5. AI 추천 → 목표 운동 → KVS 진행도 추적

추천받은 운동의 세트·횟수를 저장하고, 실제 수행량을 KVS로 비교해 리포트에 진행도를 표시합니다.

- **agent-service**: 추천 텍스트에서 KVS 추적 가능 운동(스쿼트/푸시업/런지/플랭크)의 `세트×횟수`를 정규식 추출 → `target_exercises` 응답 포함
- **backend-api**: `WorkoutRecommendation`에 `target_exercises`(JSON TEXT) 컬럼 + **Flyway V6 마이그레이션**, DTO 반영
- **frontend**:
  - ai-coach: 추천 카드에 "스쿼트 3세트×12회 바로 시작" 버튼 → `/workout?exercise=&sets=&reps=&recommendationId=`
  - /workout: 목표 수신, 운동 중 실시간 진행도 바, 종료 시 달성률 계산
  - report/detail: "추천 목표 달성도" 섹션

---

## 6. /session · /workout 페이지 통합

- 완성도 높은 `/workout`으로 일원화. 모든 네비게이션(BottomNav/Header/홈/대시보드/리포트)을 `/workout`으로 변경
- `/session`은 `/workout`으로 리다이렉트하는 페이지로 교체 (북마크 호환)

---

## 7. KVS 실시간 자세 분석 — 하드코딩 제거, 실제 MediaPipe 적용

**모션 인식 모듈: MediaPipe Pose** (`mediapipe==0.10.14`, 33 랜드마크)

기존엔 스켈레톤·점수·피드백이 **프론트·백 양쪽 모두 가짜 데이터**라 항상 같은 값만 출력됐습니다.

### 백엔드 (posture-analysis-service)
- `websocket_handler.py` **전면 재작성**: `MockPoseEstimator` → 세션별 `MediaPipePoseEstimator`(추적 상태 격리 필수) + `RepCounter` + 룰 연결. 실제 landmark·관절 각도·rep·점수·피드백을 응답에 포함. 사람 미감지 시 `pose_detected:false`
- `lunge_rule.py` **신규 작성** (프론트 4종 운동 전부 지원)
- `config.py`: `model_type` 기본값 `mock` → `mediapipe`
- 전체 룰 + feedback_service 메시지 **한국어화**

### 프론트 (frontend)
- `usePostureAnalysis.ts` **전면 재작성**: 시뮬레이션/랜덤 생성 전부 삭제, 서버 실제 landmark/score/angle/feedback/rep만 사용. WS 연결 실패 시 세션 시작 거부(가짜 폴백 없음)
- `workout/page.tsx`: 연결 실패 안내, 점수 누적은 사람 감지 시에만, 하드코딩 `avgScore:82` 폴백 제거

> 운영 주의: posture-analysis-service Pod에 MediaPipe 구동 리소스 필요. GPU 노드 사용 시 `enable_gpu` 설정 필요.

---

## 인프라 / GitOps (팀원 작업 병합)

- **gympt-infra**: AWS Chatbot Slack 연동, S3 로그 버킷 정책/액세스 로깅, CloudFront V2 액세스 로그 (head `92bb085`)
- **gympt-gitops**: CI/CD가 각 서비스 prod 이미지 태그 자동 갱신 (head `a84e1b7`)

---

## 배포 메모

- 프론트: S3 업로드까지만 (CloudFront 무효화는 보안 담당자가 별도 관리 — `create-invalidation` 금지)
- backend-api: 배포 시 Flyway가 `target_exercises` 컬럼(V6) 자동 생성
- 데모 인프라는 매일 종료/기동 (EKS 노드·ElastiCache·RDS)
