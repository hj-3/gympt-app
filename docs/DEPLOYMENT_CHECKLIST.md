# 배포 전 필수 체크리스트

## 🚨 현재 프로덕션에서 동작하지 않는 이유

Frontend가 배포되었지만 다음 설정이 **누락**되어 있습니다:

### 1. GitHub Secrets 미설정 ⚠️

```bash
# 다음 명령어로 Cognito 정보 확인
aws cognito-idp list-user-pools --max-results 10

# User Pool ID와 App Client ID를 GitHub Secrets에 추가
```

**GitHub Repository → Settings → Secrets and variables → Actions**

필요한 Secrets:
- `COGNITO_USER_POOL_ID` = `ap-northeast-2_XXXXXXXXX`
- `COGNITO_CLIENT_ID` = `XXXXXXXXXXXXXXXXXXXXXXXXXX`

### 2. Cognito User Pool이 생성되지 않았을 가능성

```bash
# Cognito User Pool 생성 확인
aws cognito-idp list-user-pools --max-results 10 --region ap-northeast-2

# 없으면 생성 필요
aws cognito-idp create-user-pool \
  --pool-name gympt-prod-users \
  --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}" \
  --auto-verified-attributes email \
  --username-attributes email \
  --region ap-northeast-2

# App Client 생성
aws cognito-idp create-user-pool-client \
  --user-pool-id ap-northeast-2_XXXXXXXXX \
  --client-name gympt-prod-web-client \
  --no-generate-secret \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --region ap-northeast-2
```

## 즉시 해결 방법

### Step 1: Cognito 정보 확인

```bash
# AWS Console 접속
# https://console.aws.amazon.com/cognito

# User Pools → 선택 → General settings
# Pool Id 복사: ap-northeast-2_XXXXXXXXX

# App clients → Show Details
# App client id 복사: XXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Step 2: GitHub Secrets 설정

```bash
# GitHub CLI 사용
gh secret set COGNITO_USER_POOL_ID --body "ap-northeast-2_XXXXXXXXX"
gh secret set COGNITO_CLIENT_ID --body "XXXXXXXXXXXXXXXXXXXXXXXXXX"

# 또는 웹 UI에서:
# Repository → Settings → Secrets → New repository secret
```

### Step 3: 재배포 트리거

```bash
git commit --allow-empty -m "chore: Trigger redeploy with Cognito configuration"
git push origin main
```

### Step 4: 배포 확인

```bash
# GitHub Actions에서 빌드 로그 확인
gh run list --limit 1

# CloudFront 배포 완료 대기 (5-10분)
# 브라우저에서 접속 테스트
```

## 배포 후 동작 테스트

### 1. 회원가입 테스트
- https://d97iz6muc3af.cloudfront.net/signup 접속
- 이메일, 비밀번호 입력 (8자 이상, 대소문자+숫자)
- 이메일 인증 코드 확인
- 로그인 성공 확인

### 2. 대시보드 접속
- https://d97iz6muc3af.cloudfront.net/dashboard
- 통계 데이터 로딩 확인 (초기에는 0으로 표시)
- 로딩 후 홈으로 리다이렉트 되지 않아야 함

### 3. 인바디 정보 입력
- 프로필 → 인바디 정보
- 키, 체중 입력
- 저장 성공 확인

### 4. AI 추천 받기
- 프로필 → AI 코치 추천
- 목표 설정 후 추천 받기
- 추천 결과 표시 확인

### 5. 운동 시작
- 운동 시작 버튼 클릭
- 카메라 권한 요청 확인
- 카메라 프리뷰 표시 확인

## 현재 알려진 제한사항

### 작동하는 기능 ✅
- 회원가입/로그인 (Cognito)
- 프로필 관리
- 인바디 정보 CRUD
- AI 운동 추천
- 대시보드 통계 (데이터가 있을 때)
- 운동 리포트 조회

### 아직 미구현 ⏳
- KVS WebRTC 실시간 스트리밍
- WebSocket 실시간 자세 피드백
- 운동 중 실시간 점수 표시
- 카메라 영상 → KVS → Posture Analysis 파이프라인

### 구현되었지만 테스트 필요 ⚠️
- Session 시작/종료
- Report 생성
- Backend API 연동

## Backend API 상태 확인

```bash
# Backend API Health Check
curl https://api.g2mpt.com/actuator/health

# Agent Service Health Check  
curl https://agent.g2mpt.com/health

# Pods 상태 확인
kubectl get pods -n prod

# Logs 확인
kubectl logs -n prod deployment/backend-api --tail=50
kubectl logs -n prod deployment/agent-service --tail=50
```

## CORS 문제 해결

Backend가 Frontend origin을 허용하도록 설정 필요:

```java
// backend-api/src/main/java/com/gympt/backend/config/WebConfig.java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
            .allowedOrigins(
                "https://d97iz6muc3af.cloudfront.net",
                "https://g2mpt.com",
                "http://localhost:3000"
            )
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*")
            .allowCredentials(true);
    }
}
```

## 모니터링

### Frontend
- CloudFront: https://console.aws.amazon.com/cloudfront
- S3 Bucket: gympt-fe-deploy-337112169365
- GitHub Actions: https://github.com/hj-3/gympt-app/actions

### Backend
- EKS Cluster: gympt-prod-eks
- ArgoCD: http://<argocd-url>
- Grafana: http://<grafana-url>

## 긴급 롤백

문제 발생 시:

```bash
# CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E14Z61F5I2E9ZM \
  --paths "/*"

# 이전 커밋으로 롤백
git revert HEAD
git push origin main
```
