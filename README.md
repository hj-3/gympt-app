# GYMPT 애플리케이션

AI 기반 개인화 운동 트레이닝 플랫폼

## 📋 프로젝트 개요

GYMPT는 AI와 컴퓨터 비전을 활용한 실시간 운동 자세 분석 및 개인화 트레이닝 플랫폼입니다.

### 주요 기능

- 🎯 **AI 기반 개인화 운동 추천** - AWS Bedrock Claude를 활용한 맞춤형 운동 계획
- 📹 **실시간 자세 분석** - MediaPipe 기반 자세 교정 및 피드백
- 📊 **운동 성과 리포트** - 데이터 기반 진행 상황 분석 및 시각화
- 🔔 **자동 복구 시스템** - 장애 자동 감지 및 복구
- 📱 **웨어러블 디바이스 연동** - 다양한 피트니스 디바이스 데이터 통합

---

## 🏗️ 아키텍처

### 서비스 구성

| 서비스 | 역할 | 기술 스택 |
|--------|------|-----------|
| **Backend API** | 사용자/운동 데이터 관리 | Spring Boot 3.2, PostgreSQL, Redis |
| **Agent Service** | AI 추천 엔진 | FastAPI, AWS Bedrock (Claude) |
| **Posture Analysis** | 실시간 자세 분석 | FastAPI, MediaPipe, OpenCV |
| **Remediation Worker** | 자동 장애 복구 | FastAPI, Kubernetes API |
| **Lambda Functions** | 서버리스 작업 처리 | Python 3.12, AWS Lambda |
| **Frontend** | 웹 애플리케이션 | Next.js 14, TypeScript |

### 기술 스택

**Backend:**
- Language: Java 21, Python 3.12
- Frameworks: Spring Boot 3.2, FastAPI 0.109
- Databases: PostgreSQL 15 (RDS), DynamoDB, ElastiCache (Redis)

**AI/ML:**
- AWS Bedrock (Claude 3 Sonnet)
- MediaPipe 0.10
- OpenCV 4.9

**Infrastructure:**
- Platform: AWS EKS (Kubernetes 1.28)
- Messaging: SQS, EventBridge
- Storage: S3, ECR
- Streaming: Kinesis Video Streams
- Monitoring: Prometheus, Grafana, CloudWatch

**Frontend:**
- Framework: Next.js 14 (App Router)
- Language: TypeScript 5.3
- Deployment: S3 + CloudFront

---

## 🚀 빠른 시작

### 사전 요구사항

```bash
# 필수 설치
- Docker Desktop 4.20+
- Docker Compose 2.20+
- Git 2.40+

# 언어별 런타임 (로컬 개발 시)
- Java 21
- Python 3.12
- Node.js 18+

# AWS CLI (배포 시)
- AWS CLI v2
- kubectl 1.28+
```

### 로컬 개발 환경

#### 1. 레포지토리 클론

```bash
git clone https://github.com/YOUR_ORG/gympt-app.git
cd gympt-app
```

#### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일 수정 (데이터베이스 연결 정보 등)
```

#### 3. Docker Compose로 전체 스택 실행

```bash
cd local
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

**실행되는 서비스:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- LocalStack (AWS emulator): `localhost:4566`
- Prometheus: `localhost:9090`
- Grafana: `localhost:3000`

#### 4. 개별 서비스 실행

**Backend API:**
```bash
cd backend-api
./gradlew bootRun
# http://localhost:8080
```

**Agent Service:**
```bash
cd agent-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
# http://localhost:8001/docs
```

**Posture Analysis Service:**
```bash
cd posture-analysis-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
# http://localhost:8002/docs
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

#### 5. API 테스트

```bash
# Health check
curl http://localhost:8080/actuator/health

# 회원가입
curl -X POST http://localhost:8080/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password1!",
    "name": "테스트유저"
  }'

# 로그인
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password1!"
  }'
```

---

## 📖 문서

### 개발 가이드

- [개발 가이드](docs/개발가이드.md) - 로컬 환경 설정, 서비스별 개발 가이드
- [아키텍처](docs/아키텍처.md) - 시스템 아키텍처, 데이터 플로우
- [API 문서](docs/API문서.md) - RESTful API 레퍼런스
- [테스트 가이드](docs/테스트가이드.md) - 단위/통합/E2E 테스트 가이드
- [배포 가이드](docs/배포가이드.md) - CI/CD 파이프라인, 배포 절차
- [보안 가이드](docs/보안가이드.md) - 환경 변수 및 Secret 관리

### 서비스별 문서

- [Backend API](backend-api/README.md) - Spring Boot API 상세 가이드
- [Agent Service](agent-service/README.md) - AI 추천 서비스 가이드
- [Posture Analysis Service](posture-analysis-service/README.md) - 자세 분석 서비스 가이드
- [Remediation Worker](remediation-worker/README.md) - 자동 복구 워커 가이드
- [Frontend](frontend/README.md) - Next.js 프론트엔드 가이드
- [Lambdas](lambdas/README.md) - Lambda 함수 목록 및 설명

---

## 🧪 테스트

### Backend API

```bash
cd backend-api
./gradlew test
./gradlew jacocoTestReport  # 커버리지 리포트
```

### Python Services

```bash
cd agent-service
pytest tests/ -v --cov=app --cov-report=html

cd posture-analysis-service
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend
npm run test           # Unit tests
npm run cypress:open   # E2E tests
```

### Lambda Functions

```bash
cd lambdas
for lambda_dir in */; do
  cd "$lambda_dir" && pytest tests/ -v && cd ..
done
```

**전체 테스트 커버리지:** 80%+ (526+ 테스트 케이스)

---

## 📦 배포

이 레포지토리는 **애플리케이션 코드**만 포함합니다. 인프라 및 배포 설정은 별도 레포지토리에서 관리됩니다:

- **gympt-infra** - Terraform 인프라 코드 (VPC, EKS, RDS, etc.)
- **gympt-gitops** - Kubernetes 매니페스트 및 Helm Charts (ArgoCD)

### CI/CD 파이프라인

**GitHub Actions Workflows:**
- `.github/workflows/backend-api-ci.yml` - Backend API 빌드/배포
- `.github/workflows/agent-service-ci.yml` - Agent Service 빌드/배포
- `.github/workflows/posture-analysis-ci.yml` - Posture Analysis 빌드/배포
- `.github/workflows/frontend-deploy.yml` - Frontend 배포 (S3/CloudFront)
- `.github/workflows/lambda-deploy.yml` - Lambda 함수 배포

**배포 프로세스:**
1. 코드 푸시 → GitHub Actions 트리거
2. 테스트 실행 → Docker 이미지 빌드
3. ECR 푸시 → GitOps 레포 업데이트
4. ArgoCD 자동 동기화 → EKS 배포

상세 배포 절차는 [배포 가이드](docs/배포가이드.md) 참고

---

## 🤝 기여하기

이 프로젝트에 기여하고 싶으시다면 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

### 개발 워크플로우

1. 이슈 생성 또는 할당받기
2. Feature 브랜치 생성 (`feature/my-feature`)
3. 코드 작성 및 테스트
4. PR 생성 (develop 브랜치로)
5. 코드 리뷰
6. Merge

### 커밋 메시지 규칙

```
<type>(<scope>): <subject>

feat(backend): 사용자 인증 API 추가
fix(agent): Bedrock API 호출 오류 수정
docs(readme): 설치 가이드 업데이트
test(posture): 자세 분석 단위 테스트 추가
```

---

## 📊 프로젝트 상태

- **버전:** 1.0.0
- **상태:** Production Ready ✅
- **테스트 커버리지:** 82%
- **마지막 배포:** 2026-05-19

### 구현 완료 서비스

- ✅ Backend API (Spring Boot)
- ✅ Agent Service (FastAPI + Bedrock)
- ✅ Posture Analysis Service (MediaPipe)
- ✅ Remediation Worker
- ✅ Frontend (Next.js)
- ✅ Lambda Functions (6개)

---

## 📝 라이선스

Proprietary - All Rights Reserved

이 프로젝트는 비공개 소유 소프트웨어입니다. 무단 복제, 배포, 수정을 금지합니다.

---

## 👥 팀

**Platform Team**
- Email: platform@gympt.com
- Slack: #gympt-dev

---

## 🔗 관련 레포지토리

- [gympt-infra](https://github.com/YOUR_ORG/gympt-infra) - Terraform 인프라 코드
- [gympt-gitops](https://github.com/YOUR_ORG/gympt-gitops) - Kubernetes 매니페스트

---

---

## 📦 버전

**Current Version:** `0.1.0`

**Changelog:** [CHANGELOG.md](../CHANGELOG.md)

---

**Last Updated:** 2026-05-19
