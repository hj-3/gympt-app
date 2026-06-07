# GYMPT Application

> 클라우드 네이티브 AI 피트니스 플랫폼 애플리케이션

[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2-green)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

---

## 📋 개요

마이크로서비스, Lambda 함수, 프론트엔드를 포함한 GYMPT 플랫폼 애플리케이션 코드입니다.

### 서비스

| 서비스 | 기술 스택 | 용도 |
|---------|-----------|---------|
| **backend-api** | Spring Boot 3.2 | 메인 REST API |
| **agent-service** | FastAPI + AWS Bedrock | AI 퍼스널 트레이닝 에이전트 |
| **posture-analysis-service** | FastAPI + MediaPipe | 실시간 자세 분석 |
| **report-service** | Python + ReportLab | PDF 리포트 생성 |
| **kvs-consumer-service** | Python + OpenCV | Kinesis Video Stream 처리 |
| **remediation-worker** | Python + Celery | 백그라운드 작업 워커 |
| **frontend** | Next.js 14 | 웹 애플리케이션 |
| **lambda/** | Python | 서버리스 함수 |

---

## 🚀 빠른 시작

### 사전 요구사항

```bash
# 백엔드 (Java)
java --version  # 17+
./gradlew --version

# Python 서비스
python --version  # 3.11+
pip --version

# 프론트엔드
node --version  # 18+
npm --version
```

### 로컬 개발

#### Backend API

```bash
cd backend-api
./gradlew bootRun
```

#### Agent Service

```bash
cd agent-service
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Posture Analysis Service

```bash
cd posture-analysis-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🐳 Docker 빌드

### 모든 서비스 빌드

```bash
# Backend API
cd backend-api
docker build -t gympt/backend-api:latest .

# Posture Analysis
cd ../posture-analysis-service
docker build -t gympt/posture-analysis-service:latest .

# Agent Service  
cd ../agent-service
docker build -t gympt/agent-service:latest .

# Report Service
cd ../report-service
docker build -t gympt/report-service:latest .

# KVS Consumer
cd ../kvs-consumer-service
docker build -t gympt/kvs-consumer-service:latest .

# Remediation Worker
cd ../remediation-worker
docker build -t gympt/remediation-worker:latest .
```

---

## 📦 ECR에 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  337112169365.dkr.ecr.ap-northeast-2.amazonaws.com

# 태그 및 푸시
docker tag gympt/backend-api:latest \
  337112169365.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/backend-api:latest
  
docker push 337112169365.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/backend-api:latest

# 다른 서비스도 반복...
```

---

## 🔄 CI/CD

### GitHub Actions 워크플로우

서비스별 CI workflow가 다음을 처리합니다:

| 서비스 | Workflow |
|---------|----------|
| backend-api | `.github/workflows/backend-api-ci.yml` |
| agent-service | `.github/workflows/agent-service-ci.yml` |
| posture-analysis-service | `.github/workflows/posture-analysis-service-ci.yml` |
| report-service | `.github/workflows/report-service-ci.yml` |
| kvs-consumer-service | `.github/workflows/kvs-consumer-service-ci.yml` |
| remediation-worker | `.github/workflows/remediation-worker-ci.yml` |

배포 흐름:

1. 테스트 및 린트 실행
2. Docker 이미지 빌드
3. **Trivy 이미지 취약점 스캔** (HIGH/CRITICAL, 리포트 모드 — 빌드 로그에 표시, 빌드는 차단하지 않음)
4. ECR에 `github.run_number-short_sha` 형식의 새 태그로 푸시 (ECR scan-on-push로 저장 단계 2차 스캔)
5. `gympt-gitops` `main` 브랜치를 checkout
6. `charts/<service>/values-dev.yaml` 또는 `values-prod.yaml`의 `.image.tag` 업데이트
7. PR 생성 없이 `gympt-gitops` `main`에 직접 커밋 및 푸시
8. ArgoCD가 Git 변경사항을 감지해 자동 배포

> 이미지 취약점은 **빌드 단계 Trivy(배포 전) + ECR scan-on-push(저장 후)** 로 이중 스캔합니다. Trivy는 현재 리포트 모드(`exit-code: 0`)이며, 구축 안정화 후 차단 모드(`'1'`)로 강화할 수 있습니다.

### 배포 트리거

```bash
# main/dev 브랜치에 커밋 및 푸시
git add .
git commit -m "feat: 새로운 기능"
git push origin main

# GitHub Actions가 자동으로 빌드 및 배포
```

`main` 브랜치는 prod values를, `dev` 브랜치는 dev values를 갱신합니다. `gympt-gitops` `main` 브랜치 direct push가 branch protection으로 막혀 있으면 `GITOPS_PAT`에 bypass 권한을 부여하거나 보호 규칙을 조정해야 합니다.

---

## 🧪 테스트

### Backend API 테스트

```bash
cd backend-api
./gradlew test
```

### Python 서비스 테스트

```bash
cd posture-analysis-service
pytest tests/
```

### Frontend 테스트

```bash
cd frontend
npm test
```

---

## 📁 서비스 상세

### Backend API

- **포트**: 8080
- **프레임워크**: Spring Boot 3.2
- **데이터베이스**: PostgreSQL
- **캐싱**: Redis
- **기능**:
  - 사용자 관리
  - 운동 추적
  - 세션 관리
  - AI 서비스와의 통합

### Posture Analysis Service

- **포트**: 8002
- **프레임워크**: FastAPI
- **ML**: MediaPipe, TensorFlow
- **하드웨어**: GPU 필요 (g4dn 인스턴스)
- **기능**:
  - 실시간 자세 감지
  - 운동 폼 분석
  - 피드백 생성

### Agent Service

- **포트**: 8003
- **프레임워크**: FastAPI
- **AI**: AWS Bedrock (Claude)
- **기능**:
  - 대화형 AI
  - 운동 권장사항
  - 개인화 코칭

### Report Service

- **포트**: 8004
- **프레임워크**: FastAPI
- **라이브러리**: ReportLab, Pandas
- **기능**:
  - PDF 리포트 생성
  - 분석 시각화
  - 진행 상황 추적

---

## 🌍 환경 변수

각 서비스는 환경별 설정을 사용합니다:

```bash
# 예시: backend-api
ENV=prod
DB_HOST=gympt-prod-postgres.xxx.rds.amazonaws.com
DB_NAME=gympt
REDIS_HOST=gympt-prod-redis.xxx.cache.amazonaws.com
AWS_REGION=ap-northeast-2
```

전체 목록은 각 서비스의 `.env.example`을 참조하세요.

---

## 📊 모니터링

### 헬스 체크

```bash
# Backend API
curl http://localhost:8080/actuator/health

# Posture Analysis
curl http://localhost:8002/health

# Agent Service
curl http://localhost:8003/health
```

### 메트릭

- Prometheus 메트릭은 `/metrics`에서 노출
- Grafana 대시보드는 monitoring 네임스페이스에 있음

---

## 🤝 기여하기

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 열기

---

## 📚 추가 문서

- 각 서비스 디렉토리의 서비스별 문서
- API 문서: `/docs` 엔드포인트 (FastAPI 서비스)
- Swagger UI: `/swagger-ui` (Spring Boot)

---

**저장소**: https://github.com/hj-3/gympt-app  
**최종 업데이트**: 2026-06-07
