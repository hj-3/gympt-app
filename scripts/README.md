# GYMPT App Scripts

> 애플리케이션 빌드 및 배포를 위한 스크립트

---

## 📋 핵심 스크립트

### 1. build-frontend.sh

**용도**: Next.js 프론트엔드 빌드 및 S3 배포

**사용법**:
```bash
./scripts/build-frontend.sh prod
./scripts/build-frontend.sh dev
```

**수행 작업**:
1. Next.js 프로젝트 빌드
2. 정적 파일 생성 (SSG)
3. S3 버킷에 업로드
4. CloudFront 캐시 무효화

**필요 환경 변수**:
```bash
# prod 환경
S3_BUCKET=gympt-frontend-prod
CLOUDFRONT_ID=E14Z61F5I2E9ZM

# dev 환경
S3_BUCKET=gympt-frontend-dev
CLOUDFRONT_ID=E14Z61F5I2E9ZM
```

---

### 2. deploy-backend.sh

**용도**: Backend API Docker 이미지 빌드 및 ECR 푸시

**사용법**:
```bash
./scripts/deploy-backend.sh prod
./scripts/deploy-backend.sh dev
```

**수행 작업**:
1. Gradle 빌드 (Spring Boot)
2. Docker 이미지 생성
3. ECR 로그인
4. 이미지 태그 및 푸시
5. (선택) GitOps 레포 업데이트

**빌드되는 이미지**:
```
{ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/backend-api:latest
{ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/backend-api:v{VERSION}
```

---

### 3. deploy-agent.sh

**용도**: Agent Service Docker 이미지 빌드 및 ECR 푸시

**사용법**:
```bash
./scripts/deploy-agent.sh prod
./scripts/deploy-agent.sh dev
```

**수행 작업**:
1. Python 의존성 설치
2. Docker 이미지 생성
3. ECR 로그인
4. 이미지 태그 및 푸시

**빌드되는 이미지**:
```
{ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/agent-service:latest
```

---

### 4. deploy-frontend.sh

**용도**: 프론트엔드 전체 배포 (빌드 + 업로드)

**사용법**:
```bash
./scripts/deploy-frontend.sh prod
./scripts/deploy-frontend.sh dev
```

**수행 작업**:
- `build-frontend.sh` 호출
- S3 동기화 상태 확인
- CloudFront 배포 상태 확인

---

### 5. check-project.sh

**용도**: 애플리케이션 프로젝트 구조 검증

**사용법**:
```bash
./scripts/check-project.sh
```

**검증 항목**:
- 서비스 디렉토리 구조
- Dockerfile 존재 여부
- 필수 설정 파일
- 의존성 파일

---

## 🚀 일반적인 사용 순서

### 수동 배포 (CI/CD 없이)

```bash
# 1. ECR 로그인
AWS_REGION="ap-northeast-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 2. Backend API 배포
./scripts/deploy-backend.sh prod

# 3. Agent Service 배포
./scripts/deploy-agent.sh prod

# 4. Frontend 배포
./scripts/deploy-frontend.sh prod

# 5. ArgoCD 동기화 (또는 자동 동기화 대기)
argocd app sync backend-api-prod
argocd app sync agent-service-prod

# 6. 배포 확인
kubectl get pods -n gympt-prod
```

### 로컬 개발

```bash
# Backend API
cd backend-api
./gradlew bootRun

# Agent Service
cd agent-service
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 🔄 CI/CD 워크플로우

GitHub Actions가 자동으로 빌드 및 배포를 처리합니다:

```
개발자 커밋 & 푸시
  ↓
GitHub Actions 트리거
  ↓
1. 테스트 실행
2. Docker 이미지 빌드
3. ECR 푸시
4. gympt-gitops values 업데이트
  ↓
ArgoCD 자동 동기화
  ↓
EKS 클러스터 배포
```

**GitHub Secrets 필요**:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION=ap-northeast-2
```

---

## 📦 아카이브된 스크립트

다음 스크립트들은 `archive/`로 이동되었습니다:

| 스크립트 | 이동 사유 |
|---------|----------|
| **build-all-services.sh** | 개별 배포 스크립트로 분리 |
| **deploy-all.sh** | CI/CD로 자동화 |
| **verify-deployment.sh** | 루트 verify-cluster.sh로 통합 |

**아카이브 접근**:
```bash
ls scripts/archive/
```

---

## 🔧 트러블슈팅

### build-frontend.sh 실패

```bash
# 수동 빌드
cd frontend
npm install
npm run build

# S3 업로드
aws s3 sync out/ s3://gympt-frontend-prod/ --delete

# CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E14Z61F5I2E9ZM \
  --paths "/*"
```

### deploy-backend.sh 실패

```bash
# 수동 빌드
cd backend-api
./gradlew clean build

# Docker 빌드
docker build -t backend-api:latest .

# ECR 푸시
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
docker tag backend-api:latest \
  ${ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/backend-api:latest

docker push ${ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/backend-api:latest
```

### ECR 로그인 실패

```bash
# 권한 확인
aws ecr describe-repositories --region ap-northeast-2

# 재로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-2.amazonaws.com
```

---

## 📁 서비스별 구조

```
gympt-app/
├── backend-api/           # Spring Boot
│   ├── Dockerfile
│   ├── build.gradle
│   └── src/
│
├── agent-service/         # FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── posture-analysis-service/  # FastAPI + MediaPipe
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── frontend/              # Next.js
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│
└── scripts/
    ├── build-frontend.sh
    ├── deploy-backend.sh
    ├── deploy-agent.sh
    └── deploy-frontend.sh
```

---

## 🧪 테스트

### 로컬 테스트

```bash
# Backend API
cd backend-api
./gradlew test

# Python 서비스
cd agent-service
pytest tests/

# Frontend
cd frontend
npm test
```

### Docker 이미지 테스트

```bash
# Backend API
docker build -t backend-api:test backend-api/
docker run -p 8080:8080 backend-api:test

# Agent Service
docker build -t agent-service:test agent-service/
docker run -p 8003:8003 agent-service:test
```

---

## 📖 관련 문서

- **[../README.md](../README.md)** - 애플리케이션 개요
- **[../docs/API문서.md](../docs/API문서.md)** - API 참조
- **[../../DEPLOYMENT_GUIDE.md](../../DEPLOYMENT_GUIDE.md)** - 완전한 배포 가이드
- **[../../scripts/README.md](../../scripts/README.md)** - 루트 스크립트 가이드

---

**최종 업데이트**: 2026-06-02  
**관리**: Application Team
