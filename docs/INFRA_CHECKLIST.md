# GYMPT 인프라 체크리스트

> 작성일: 2026-06-01  
> 목적: 서비스 완전 기동 및 인프라 안정화를 위한 잔여 작업 추적

---

## 🔴 1순위 — 서비스 기동 완료

- [ ] **GitHub Actions Variables 설정** (프론트엔드 CI 배포 필수)
  - `FRONTEND_BUCKET_PROD` = `gympt-fe-deploy-337112169365`
  - `CLOUDFRONT_DISTRIBUTION_ID_PROD` = `E14Z61F5I2E9ZM`
  - 경로: `github.com/hj-3/gympt-app` → Settings → Secrets and variables → Actions → Variables

- [ ] **PR #24 merge 후 backend-api 재배포 확인**
  - CI 빌드 → ECR push → gitops PR 생성 → merge → ArgoCD 배포
  - 확인: `kubectl get pods -n gympt-prod`

- [ ] **frontend CI 배포 확인**
  - Actions 탭에서 `Frontend Deploy` 워크플로우 성공 여부 확인
  - CloudFront 캐시 무효화 완료 여부 확인

- [ ] **전체 서비스 헬스체크**
  - `https://api.g2mpt.com/actuator/health` → 200 OK
  - `https://g2mpt.com` → 프론트엔드 로딩 확인
  - 로그인 → 대시보드 → 인바디 → 운동 세션 플로우 테스트

---

## 🔴 2순위 — 코드·설정 동기화 (당장 적용 필요)

- [ ] **gympt-gitops 로컬 변경사항 커밋·PR**
  - `charts/posture-analysis-service/values-prod.yaml`
  - `platform/karpenter/provisioner.yaml`
  - `platform/network-policies/posture-analysis-netpol.yaml` (ml-models 네임스페이스 참조 수정)

- [ ] **gympt-infra 로컬 변경사항 커밋·PR**
  - `terraform/modules/iam/main.tf` — account ID 변수화
  - `terraform/modules/rds/main.tf` — egress 0.0.0.0/0 → VPC CIDR
  - `terraform/modules/elasticache/main.tf` — egress 0.0.0.0/0 → VPC CIDR
  - `terraform/modules/eks/main.tf` — Karpenter↔관리형노드 cross-SG 룰 코드화
  - `terraform/environments/prod/main.tf` — S3 버킷명·CloudFront ID·EKS CIDR 변수화
  - `terraform/environments/dev/main.tf` — EKS public_access_cidrs 변수화

- [ ] **terraform import → plan → apply**
  - 수동으로 추가한 cross-SG 룰을 state에 import 후 apply
  ```bash
  terraform import 'module.eks.aws_security_group_rule.node_ingress_from_cluster_sg' sgr-0fda49257a46476b7
  terraform import 'module.eks.aws_security_group_rule.cluster_sg_ingress_from_node' sgr-01938b640d0226035
  terraform plan  # 반드시 plan 먼저 검토
  terraform apply
  ```

---

## 🟡 3순위 — 기능 완성 (서비스는 뜨지만 일부 기능 미동작)

- [ ] **Secrets Manager 누락 시크릿 생성**
  - `gympt/prod/agent-service` — backend_api_key, redis 정보, DynamoDB 테이블명
  - `gympt/prod/remediation-worker` — backend_api_url, backend_api_key
  - 생성 후 ExternalSecret 강제 동기화:
    ```bash
    kubectl annotate externalsecret agent-service-secrets -n gympt-prod force-sync=$(date +%s) --overwrite
    kubectl annotate externalsecret remediation-worker-secrets -n gympt-prod force-sync=$(date +%s) --overwrite
    ```

- [ ] **posture-analysis-service GPU 모드 활성화**
  - 현재: `GPU Enabled: False` (CPU 모드 동작 중)
  - 원인: Node Feature Discovery(NFD) 미설치로 GPU 감지 실패
  - 해결: NFD Helm 설치 또는 Karpenter NodePool에 GPU 인스턴스 추가

---

## 🟡 4순위 — 인프라 보안·안정화

- [ ] **VPC Endpoint 추가** (현재 NAT Gateway 경유 → 비용 발생)
  - 대상: Secrets Manager, SQS, DynamoDB, CloudWatch Logs
  - Terraform `vpc` 모듈에 `aws_vpc_endpoint` 리소스 추가

- [ ] **EKS API 엔드포인트 IP 제한**
  - 현재: `public_access_cidrs = ["0.0.0.0/0"]`
  - 변경: `terraform.tfvars`에서 운영자/VPN IP로 제한
  ```hcl
  eks_public_access_cidrs = ["YOUR_IP/32"]
  ```

- [ ] **GPU 노드 Kubernetes 버전 업그레이드**
  - 현재: GPU 노드 v1.32.9, 일반 노드 v1.35.5 (불일치)
  - AWS 콘솔 또는 Terraform으로 GPU 노드 그룹 버전 업그레이드

---

## 🟢 5순위 — ArgoCD·보안 설정 개선

- [ ] **ArgoCD sourceRepos 와일드카드 제거**
  - `argocd/projects/gympt-platform.yaml` — `['*']` → 특정 저장소 목록으로 변경

- [ ] **backend-api Prometheus 엔드포인트 인증 추가**
  - `SecurityConfig.java` — `/actuator/prometheus` 공개 노출 → 내부 네트워크만 허용

- [ ] **posture-analysis-service NetworkPolicy 수정**
  - `platform/network-policies/posture-analysis-netpol.yaml`
  - 존재하지 않는 `ml-models` 네임스페이스 참조 제거

---

## 진단 명령어 모음

```bash
# 전체 Pod 상태
kubectl get pods -n gympt-prod

# ExternalSecret 상태
kubectl get externalsecret -n gympt-prod

# ALB / Ingress 상태
kubectl get ingress -n gympt-prod

# ArgoCD 앱 상태
kubectl get application -n argocd

# Karpenter 노드
kubectl get nodeclaim && kubectl get nodepool

# API 헬스체크
curl https://api.g2mpt.com/actuator/health
```
