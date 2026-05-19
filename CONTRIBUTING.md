# GYMPT 기여 가이드

GYMPT 프로젝트에 기여해주셔서 감사합니다! 이 문서는 효과적인 협업을 위한 가이드라인을 제공합니다.

## 목차

1. [시작하기](#시작하기)
2. [개발 워크플로우](#개발-워크플로우)
3. [코드 스타일](#코드-스타일)
4. [커밋 규칙](#커밋-규칙)
5. [Pull Request](#pull-request)
6. [코드 리뷰](#코드-리뷰)
7. [테스트](#테스트)

---

## 시작하기

### 개발 환경 설정

1. **레포지토리 Fork 및 Clone**

```bash
# Fork: GitHub UI에서 Fork 버튼 클릭

# Clone
git clone https://github.com/YOUR_USERNAME/gympt-app.git
cd gympt-app

# Upstream 설정
git remote add upstream https://github.com/YOUR_ORG/gympt-app.git
```

2. **로컬 개발 환경 구성**

[개발 가이드](docs/개발가이드.md)를 참고하여 로컬 환경을 설정하세요.

```bash
# 환경 변수 설정
cp .env.example .env

# Docker Compose 실행
cd local
docker-compose up -d
```

3. **의존성 설치**

```bash
# Backend API
cd backend-api && ./gradlew build

# Python Services
cd agent-service && pip install -r requirements.txt -r requirements-dev.txt

# Frontend
cd frontend && npm install
```

---

## 개발 워크플로우

### 브랜치 전략

```
main (protected)
  ├── develop (default branch)
  │   ├── feature/user-authentication
  │   ├── feature/workout-recommendation
  │   ├── bugfix/session-timeout
  │   └── refactor/api-error-handling
  └── hotfix/critical-bug-fix
```

**브랜치 명명 규칙:**
- `feature/<feature-name>` - 새로운 기능
- `bugfix/<bug-name>` - 버그 수정
- `hotfix/<critical-fix>` - 긴급 수정 (main에서 분기)
- `refactor/<refactor-name>` - 리팩토링
- `docs/<doc-update>` - 문서 업데이트

### 작업 프로세스

1. **이슈 확인 또는 생성**

```bash
# GitHub Issues에서 작업할 이슈 선택 또는 생성
# 이슈 번호: #123
```

2. **최신 develop 브랜치 동기화**

```bash
git checkout develop
git pull upstream develop
```

3. **Feature 브랜치 생성**

```bash
git checkout -b feature/user-authentication
```

4. **개발 진행**

```bash
# 코드 작성
# 테스트 작성 및 실행
# 로컬에서 검증
```

5. **커밋**

```bash
git add .
git commit -m "feat(backend): JWT 기반 사용자 인증 구현

- JWT 토큰 생성 및 검증 로직 추가
- Spring Security 설정
- 단위 테스트 추가 (80% 커버리지)

Closes #123"
```

6. **푸시 및 PR 생성**

```bash
git push origin feature/user-authentication

# GitHub에서 PR 생성
# Base: develop ← Compare: feature/user-authentication
```

---

## 코드 스타일

### Java (Spring Boot)

**Google Java Style Guide 준수**

```java
// 좋은 예시
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class UserService {
    
    private final UserRepository userRepository;
    
    /**
     * 사용자 조회
     * 
     * @param userId 사용자 ID
     * @return 사용자 정보
     * @throws UserNotFoundException 사용자를 찾을 수 없을 때
     */
    public User findById(Long userId) {
        return userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException(userId));
    }
}
```

**체크:**
- Checkstyle 설정 준수
- 불필요한 주석 제거
- 의미 있는 변수/메서드 이름
- 한 메서드는 한 가지 역할만

### Python (FastAPI)

**PEP 8 준수 + Black 포맷터**

```python
# 좋은 예시
from typing import Optional
from fastapi import HTTPException

async def get_user_profile(user_id: int) -> dict:
    """
    사용자 프로필 조회
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        사용자 프로필 딕셔너리
        
    Raises:
        HTTPException: 사용자를 찾을 수 없을 때
    """
    profile = await db.fetch_user(user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found"
        )
    return profile
```

**체크:**
- Black 포맷터 적용
- Flake8 린트 통과
- Type hints 사용
- Docstring 작성 (함수/클래스)

### TypeScript (Frontend)

**Airbnb Style Guide 준수**

```typescript
// 좋은 예시
interface WorkoutCardProps {
  workout: Workout;
  onStart: (workoutId: number) => void;
}

export const WorkoutCard: React.FC<WorkoutCardProps> = ({ workout, onStart }) => {
  const handleClick = () => {
    onStart(workout.id);
  };
  
  return (
    <div className="workout-card">
      <h3>{workout.title}</h3>
      <button onClick={handleClick}>시작</button>
    </div>
  );
};
```

**체크:**
- ESLint 설정 준수
- Prettier 포맷터 적용
- TypeScript strict mode
- PropTypes 또는 Interface 정의

### 코드 포맷팅

```bash
# Java (Google Java Format)
./gradlew googleJavaFormat

# Python (Black + isort)
black .
isort .

# TypeScript (Prettier)
npm run format
```

---

## 커밋 규칙

### Conventional Commits 사용

**형식:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 변경

**Scope (선택적):**
- `backend`, `agent`, `posture`, `frontend`, `lambda`, `docs`, etc.

**예시:**

```bash
# 기능 추가
feat(backend): 사용자 프로필 조회 API 추가

GET /api/v1/users/{userId} 엔드포인트 구현
- UserController, UserService 추가
- JPA Repository 활용
- 단위 테스트 및 통합 테스트 추가

Closes #123

# 버그 수정
fix(agent): Bedrock API 호출 시 타임아웃 오류 수정

boto3 클라이언트 타임아웃 설정 추가 (30초 → 60초)
재시도 로직 개선 (exponential backoff)

Fixes #456

# 문서 업데이트
docs(readme): 로컬 개발 환경 설정 가이드 추가

Docker Compose 실행 방법 및 트러블슈팅 내용 추가

# 리팩토링
refactor(posture): MediaPipe 초기화 로직 개선

코드 중복 제거 및 성능 개선
테스트 코드 유지
```

### 커밋 메시지 체크리스트

- [ ] Type과 Scope 명확히 작성
- [ ] Subject는 50자 이내, 명령형 동사 사용
- [ ] Body에 "왜" 변경했는지 설명 (선택적)
- [ ] 관련 이슈 번호 포함 (`Closes #123`, `Fixes #456`)
- [ ] 한글 사용 (팀 내부 프로젝트)

---

## Pull Request

### PR 생성 전 체크리스트

- [ ] 최신 develop 브랜치와 동기화
- [ ] 로컬에서 모든 테스트 통과
- [ ] 코드 포맷팅 완료
- [ ] 불필요한 디버그 코드 제거
- [ ] .env, secrets 파일 커밋 안 됨

### PR 템플릿

```markdown
## 변경 사항
<!-- 무엇을 변경했는지 간략히 설명 -->

## 변경 이유
<!-- 왜 이 변경이 필요한지 설명 -->

## 테스트 계획
- [ ] 단위 테스트 추가/수정
- [ ] 통합 테스트 추가/수정
- [ ] 로컬에서 수동 테스트 완료
- [ ] Postman/curl로 API 테스트 완료

## 관련 이슈
Closes #123

## 스크린샷 (UI 변경 시)
<!-- 스크린샷 첨부 -->

## 체크리스트
- [ ] 코드 포맷팅 완료
- [ ] 테스트 커버리지 80% 이상
- [ ] 문서 업데이트 (필요 시)
- [ ] 브레이킹 체인지 없음 (또는 명시)
```

### PR 크기 가이드라인

- **Small PR (권장):** 변경 라인 수 < 300
- **Medium PR:** 300-500 라인
- **Large PR (지양):** > 500 라인

큰 PR은 여러 개로 분할하는 것을 권장합니다.

---

## 코드 리뷰

### 리뷰어 가이드라인

**리뷰 시 확인 사항:**

1. **기능 정상 동작**
   - 요구사항 충족
   - 엣지 케이스 처리

2. **코드 품질**
   - 가독성
   - 유지보수성
   - SOLID 원칙 준수

3. **테스트**
   - 테스트 커버리지
   - 테스트 품질

4. **보안**
   - SQL Injection, XSS 등 취약점
   - 인증/인가 적절히 구현
   - Secret 하드코딩 없음

5. **성능**
   - N+1 쿼리 없음
   - 불필요한 API 호출 없음
   - 효율적인 알고리즘

**리뷰 코멘트 예시:**

```markdown
# 👍 칭찬
좋은 접근 방법입니다! 가독성이 매우 높습니다.

# 💡 제안
이 부분은 Stream API를 사용하면 더 간결할 것 같습니다.

# ❓ 질문
이 로직이 필요한 이유를 설명해주실 수 있나요?

# 🚨 필수 변경 요청
보안 이슈: 패스워드가 로그에 노출되고 있습니다.

# 🐛 버그
null 체크가 누락되어 NPE가 발생할 수 있습니다.
```

### 리뷰이 가이드라인

- 리뷰 코멘트에 정중하게 응답
- 피드백을 반영하거나 이유 설명
- "Done", "Fixed"보다 구체적인 응답
- 불명확한 코멘트는 추가 질문

### 승인 기준

- 최소 1명의 Approve 필요
- 모든 코멘트 해결
- CI 테스트 통과
- Merge conflicts 없음

---

## 테스트

### 테스트 작성 원칙

1. **AAA 패턴 사용**
   - Arrange (준비)
   - Act (실행)
   - Assert (검증)

2. **독립적인 테스트**
   - 테스트 간 의존성 없음
   - 실행 순서 무관

3. **명확한 테스트 이름**
   - `메서드명_시나리오_예상결과`
   - 예: `createUser_duplicateEmail_throwsException`

4. **커버리지 목표**
   - 신규 코드: 80% 이상
   - 전체 프로젝트: 80% 유지

### 테스트 실행

```bash
# Backend API
cd backend-api
./gradlew test
./gradlew jacocoTestReport

# Python Services
cd agent-service
pytest tests/ -v --cov=app --cov-report=html

# Frontend
cd frontend
npm run test
npm run test:coverage
```

### CI에서 테스트 자동 실행

PR 생성 시 GitHub Actions가 자동으로 테스트 실행합니다.
모든 테스트가 통과해야 Merge 가능합니다.

---

## 문의

질문이나 제안사항이 있으시면:

- **Slack:** #gympt-dev
- **Email:** platform@gympt.com
- **GitHub Issues:** 이슈 생성

---

**감사합니다!** 🎉

여러분의 기여가 GYMPT를 더 나은 플랫폼으로 만듭니다.
