# GYMPT App Scripts

서비스 빌드, 배포, 검증을 위한 스크립트 모음입니다.

---

## Prod 환경 앱 배포 순서

> **선행 조건**: `gympt-gitops`의 STEP 6~17 완료 (ArgoCD와 플랫폼 서비스가 정상 동작 중)

---

### STEP 18 — ECR 이미지 초기 Push (CI/CD 전 수동 배포 시)

GitHub Actions CI/CD가 설정되어 있으면 이 단계는 건너뜁니다.
처음 배포하거나 수동으로 이미지를 올릴 때만 실행합니다.

```bash
cd gympt-app

AWS_REGION="ap-northeast-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# ECR 로그인
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# 서비스별 빌드 & Push
./scripts/build-all-services.sh prod
```

또는 서비스별 개별 배포:

```bash
# Backend API
./scripts/deploy-backend.sh prod

# Agent Service
./scripts/deploy-agent.sh prod

# Frontend (S3 + CloudFront)
./scripts/deploy-frontend.sh prod
```

---

### STEP 19 — ArgoCD 앱 동기화 확인

```bash
# ArgoCD 전체 앱 상태 확인
kubectl get applications -n argocd

# 특정 앱 강제 동기화
argocd app sync backend-api-prod
argocd app sync agent-service-prod

# 모든 앱 동기화 대기
argocd app wait --all --health --timeout 600
```

---

### STEP 20 — 서비스 동작 확인

```bash
# Pod 상태
kubectl get pods -n gympt-prod

# 로그 확인
kubectl logs -f deployment/backend-api-prod -n gympt-prod
kubectl logs -f deployment/agent-service-prod -n gympt-prod

# Ingress 확인 (ALB 엔드포인트)
kubectl get ingress -n gympt-prod
```

---

### STEP 21 — 배포 검증

```bash
./scripts/verify-deployment.sh prod
```

---

## 전체 배포 순서 요약 (3개 레포)

```
[gympt-infra]
  STEP 1  init-backend.sh                    Terraform 백엔드 생성
  STEP 2  terraform init                     백엔드 연결
  STEP 3  terraform apply (단계적)            인프라 프로비저닝
  STEP 4  get-kubeconfig.sh prod             kubectl 연결
  STEP 5  check-resources.sh prod            인프라 상태 확인

[gympt-gitops]
  STEP 6  install-platform.sh prod           ArgoCD + ESO + Prometheus
  STEP 7  AWS Secrets Manager 시크릿 생성    (수동 작업)
  STEP 8  ESO values ACCOUNT_ID 업데이트    helm upgrade
  STEP 9  cluster-secret-store.yaml         ClusterSecretStore 적용
  STEP 10 namespace-labels.yaml             네임스페이스 + 레이블
  STEP 11 provisioner.yaml                  Karpenter NodePool
  STEP 12 argocd/projects/*.yaml            ArgoCD 프로젝트 등록
  STEP 13 apply-network-policies.sh prod    NetworkPolicy 적용
  STEP 14 argocd/app-of-apps/prod-apps.yaml 앱 배포 트리거
  STEP 15 platform/monitoring/*             ServiceMonitor + PrometheusRule
  STEP 16 kubectl get applications          ArgoCD 상태 확인
  STEP 17 test-connectivity.sh              서비스 간 통신 테스트

[gympt-app]
  STEP 18 build-all-services.sh prod        이미지 빌드 & ECR Push (수동시)
  STEP 19 argocd app sync                   ArgoCD 동기화
  STEP 20 kubectl get pods -n gympt-prod    Pod 상태 확인
  STEP 21 verify-deployment.sh prod         최종 검증
```

---

## CI/CD 자동 배포 흐름

수동 배포 없이 GitHub Actions를 통해 자동 배포됩니다.

```
개발자 main 브랜치 push
  │
  ▼
GitHub Actions 트리거 (각 서비스별 ci.yml)
  │  1. 테스트 실행
  │  2. Docker 이미지 빌드
  │  3. ECR Push (ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-prod/SERVICE:TAG)
  │  4. gympt-gitops 레포의 values-prod.yaml image.tag 업데이트
  │
  ▼
ArgoCD가 변경 감지 → 자동 Helm Upgrade
  │
  ▼
gympt-prod 네임스페이스에 Rolling Update
```

---

## 스크립트 참조

| 스크립트 | 설명 | 사용법 |
|----------|------|--------|
| `build-all-services.sh` | 전체 서비스 빌드 & ECR Push | `./scripts/build-all-services.sh prod` |
| `deploy-backend.sh` | Backend API 수동 배포 | `./scripts/deploy-backend.sh prod` |
| `deploy-agent.sh` | Agent Service 수동 배포 | `./scripts/deploy-agent.sh prod` |
| `deploy-frontend.sh` | Frontend S3+CloudFront 배포 | `./scripts/deploy-frontend.sh prod` |
| `deploy-all.sh` | 전체 서비스 일괄 배포 | `./scripts/deploy-all.sh prod` |
| `verify-deployment.sh` | 배포 상태 검증 | `./scripts/verify-deployment.sh prod` |
| `check-project.sh` | 프로젝트 구조 확인 | `./scripts/check-project.sh` |
