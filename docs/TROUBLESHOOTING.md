# Frontend 문제 해결 가이드

## 현재 발견된 문제들

### 1. 로딩 후 홈화면으로 리다이렉트 ❌

**증상**: 대시보드, /session 등 보호된 페이지 접근 시 로딩만 하다가 홈으로 돌아감

**원인**:
- Cognito 인증 실패
- `ProtectedRoute`가 `user`가 없으면 `/login`으로 리다이렉트
- 로그인 페이지가 다시 홈으로 리다이렉트

**진단 방법**:
```bash
# 1. 브라우저 개발자 도구 Console 확인
# 에러 메시지 확인

# 2. Network 탭 확인  
# Cognito API 호출 실패 여부 확인

# 3. 환경 변수 확인
echo $NEXT_PUBLIC_COGNITO_USER_POOL_ID
echo $NEXT_PUBLIC_COGNITO_CLIENT_ID
```

**해결 방법**:

#### Option 1: Cognito Secrets 확인 (GitHub Actions)
```bash
# GitHub Repository → Settings → Secrets and variables → Actions
# 다음 secrets이 설정되어 있는지 확인:
COGNITO_USER_POOL_ID=ap-northeast-2_XXXXXXXXX
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

#### Option 2: 로컬 테스트용 .env 파일 생성
```bash
# frontend/.env.local 생성
NEXT_PUBLIC_API_URL=https://api.g2mpt.com
NEXT_PUBLIC_COGNITO_USER_POOL_ID=ap-northeast-2_XXXXXXXXX
NEXT_PUBLIC_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
NEXT_PUBLIC_AWS_REGION=ap-northeast-2
NEXT_PUBLIC_ENV=prod
```

### 2. /session 페이지 작동 안함 ❌

**증상**: 카메라 시작 버튼 클릭해도 반응 없음

**원인**:
1. 인증 실패로 페이지 자체가 로드 안됨
2. API 호출 실패 (`getTodayRoutine` 404)

**해결 방법**:

#### 먼저 인증 문제 해결 (위 참조)

#### 루틴이 없을 때 처리 추가
```typescript
// Session 페이지 수정 필요
// 루틴이 없으면 기본 루틴 생성하거나 루틴 없이 시작 가능하게
```

### 3. 대시보드 로딩 후 홈 리다이렉트 ❌

**원인**: 위와 동일 - 인증 실패

### 4. 인바디 정보 탭 접근 불가 ❌

**증상**: `/profile/body` 접근 시 에러 또는 리다이렉트

**원인**:
1. 인증 실패
2. API 호출 실패 (404)

**해결**: 
- 인증 문제 해결 후
- 404는 정상 (데이터 없을 때) - empty state 표시해야 함

### 5. AI 추천 못 받아옴 ❌

**증상**: "새로운 추천 받기" 클릭 시 에러

**원인**:
1. Agent Service API 엔드포인트 설정 누락
2. Bedrock 권한 문제

**확인 사항**:
```bash
# Agent Service가 실행 중인지 확인
kubectl get pods -n prod | grep agent-service

# Agent Service 로그 확인
kubectl logs -n prod deployment/agent-service --tail=50

# Bedrock IAM 권한 확인
aws iam get-role --role-name prod-bedrock-agent-role
```

## 해결 우선순위

### 1단계: Cognito 설정 확인 (가장 중요!)

모든 문제의 근본 원인입니다.

```bash
# AWS Console에서 확인
# Cognito → User Pools → 해당 풀 선택
# Pool ID와 App Client ID 확인

# GitHub Secrets 설정
gh secret set COGNITO_USER_POOL_ID --body "ap-northeast-2_XXXXXXXXX"
gh secret set COGNITO_CLIENT_ID --body "XXXXXXXXXXXXXXXXXXXXXXXXXX"

# 재배포
git commit --allow-empty -m "Trigger redeploy with Cognito secrets"
git push
```

### 2단계: API 엔드포인트 확인

```bash
# Backend API 상태 확인
kubectl get svc -n prod | grep backend-api

# Ingress 확인
kubectl get ingress -n prod

# 실제 API 테스트
curl https://api.g2mpt.com/actuator/health
```

### 3단계: Agent Service 엔드포인트 추가

현재 frontend가 agent service URL을 모릅니다.

```yaml
# .github/workflows/frontend-deploy.yml 수정 필요
env:
  NEXT_PUBLIC_API_URL: ${{ steps.env.outputs.api_url }}
  NEXT_PUBLIC_AGENT_API_URL: https://agent.g2mpt.com  # 추가
```

### 4단계: CORS 설정 확인

Backend가 Frontend origin을 허용하는지 확인

```java
// backend-api CORS 설정 확인 필요
@CrossOrigin(origins = ["https://d97iz6muc3af.cloudfront.net"])
```

## 임시 우회 방법 (개발용)

인증 없이 테스트하려면:

```typescript
// ProtectedRoute.tsx 임시 수정 (프로덕션에서는 절대 사용 금지!)
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // 임시로 인증 체크 비활성화
  return <>{children}</>;
}
```

## 체크리스트

프로덕션 배포 전 확인사항:

- [ ] Cognito User Pool 생성 완료
- [ ] Cognito App Client 생성 완료  
- [ ] GitHub Secrets 설정 (COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID)
- [ ] Backend API 배포 완료 및 접근 가능
- [ ] Agent Service 배포 완료 및 접근 가능
- [ ] Backend CORS 설정 완료
- [ ] CloudFront에 Frontend 배포 완료
- [ ] 회원가입 테스트 성공
- [ ] 로그인 테스트 성공
- [ ] API 호출 테스트 성공

## 로그 확인 방법

### Frontend (브라우저)
```
개발자 도구 → Console
개발자 도구 → Network → Filter: Fetch/XHR
```

### Backend API
```bash
kubectl logs -n prod deployment/backend-api --tail=100 --follow
```

### Agent Service
```bash
kubectl logs -n prod deployment/agent-service --tail=100 --follow
```

### ArgoCD
```bash
# Sync 상태 확인
argocd app get prod-frontend
argocd app get prod-backend-api
argocd app get prod-agent-service
```
