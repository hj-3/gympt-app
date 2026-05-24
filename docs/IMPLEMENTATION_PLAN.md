# Frontend 완성도 개선 계획

## 발견된 문제점

### 1. 기본 신체 정보 수정 불가 ❌
- **위치**: `/profile/info`
- **문제**: "수정" 버튼이 있지만 실제 동작하지 않음
- **해결방안**: 인바디 정보에 통합, profile/info에서는 기본 정보만 표시

### 2. 인바디 정보 페이지 접근 오류 ❌
- **위치**: `/profile/body`
- **문제**: API 호출 실패 또는 404 처리 미흡
- **해결방안**: 
  - 404 에러 시 empty state 정상 표시
  - 최신 데이터 없을 때 add 페이지로 유도

### 3. AI 추천 Bedrock 연동 미확인 ⚠️
- **백엔드**: Agent Service Bedrock 연동 완료
- **프론트엔드**: API 호출 구현됨
- **문제**: 실제 테스트 필요
- **필요 데이터**:
  - 사용자 프로필 (user_id, name, email)
  - 인바디 정보 (height, weight, body_fat, muscle_mass)
  - 운동 목표 (goal, fitness_level, days_per_week)
  - 부상/제한사항 (injuries_or_limitations)

### 4. /session 페이지 미구현 ❌
- **위치**: `/session`
- **문제**: 페이지 자체가 없거나 카메라 권한 요청 없음
- **필요 기능**:
  - 카메라 권한 요청
  - KVS WebRTC 연결
  - 실시간 자세 분석
  - WebSocket을 통한 피드백 수신

### 5. 미연동 Backend API 확인 필요 ❓
- Workout Routine API
- Workout Session API  
- Stats/Dashboard API
- Report API

## 해결 순서

1. ✅ Profile Info 페이지 간소화 (신체 정보 제거)
2. ✅ Body Profile 404 처리 개선
3. ✅ Session 페이지 구현 (카메라 권한, KVS WebRTC)
4. ✅ Backend API 연동 확인 및 구현
5. ✅ AI 추천 데이터 보강 (user profile + body profile)

## Backend API 목록

### 이미 연동됨 ✅
- `POST /api/v1/body-profiles` - 인바디 등록
- `GET /api/v1/body-profiles/latest` - 최신 인바디 조회
- `GET /api/v1/body-profiles/history` - 인바디 이력
- `POST /agent/workout/recommend` - AI 운동 추천

### 연동 필요 🔲
- `GET /api/v1/routines/today/{userId}` - 오늘의 루틴
- `GET /api/v1/routines/{userId}` - 루틴 목록
- `POST /api/v1/sessions/start` - 세션 시작
- `POST /api/v1/sessions/{id}/complete` - 세션 완료
- `GET /api/v1/sessions/{id}` - 세션 조회
- `GET /api/v1/reports/{sessionId}` - 리포트 조회
- `GET /api/v1/reports/user/{userId}` - 리포트 목록
- `GET /api/v1/stats/{userId}` - 통계 조회
- `GET /api/v1/stats/{userId}/weekly` - 주간 통계
- `GET /api/v1/kvs/credentials/{sessionId}` - KVS 자격증명

## 구현 계획

### Phase 1: 기본 정보 수정 (30분)
1. profile/info 신체 정보 섹션 제거
2. body profile 페이지를 신체 정보 관리 페이지로 통합

### Phase 2: Session 페이지 구현 (2시간)
1. session/page.tsx 생성
2. 카메라 권한 요청 컴포넌트
3. KVS WebRTC 연결 로직
4. 실시간 자세 분석 뷰
5. WebSocket 피드백 수신

### Phase 3: Dashboard API 연동 (1시간)
1. Stats API 연동
2. Weekly Progress 차트
3. Recent Sessions 목록

### Phase 4: AI 추천 데이터 보강 (30분)
1. Body Profile 데이터 함께 전송
2. User Profile 정보 추가
3. 추천 결과 포맷팅 개선

### Phase 5: E2E 테스트 (1시간)
1. 회원가입 → 인바디 입력 → AI 추천
2. 운동 시작 → 실시간 피드백
3. 세션 완료 → 리포트 확인
