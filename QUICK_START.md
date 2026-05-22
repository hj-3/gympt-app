# GYMPT 시스템 점검 빠른 가이드

## 🚀 빠른 시작

### 전체 시스템 상태 확인 (가장 먼저 실행)

```bash
# 1. EKS 클러스터 연결 설정
aws eks update-kubeconfig --region ap-northeast-2 --name gympt-dev

# 2. 전체 시스템 헬스 체크
./scripts/system-health-check.sh

# 3. 프론트엔드 배포 상태 확인
./scripts/frontend-health-check.sh prod
```

---

## 📋 문제별 빠른 해결법

### 🌐 프론트엔드가 안 보이는 경우

```bash
# 1. S3 버킷 확인
aws s3 ls s3://gympt-fe-deploy-337112169365/

# 파일이 없다면 → 재배포
cd frontend
npm install
npm run build:prod
aws s3 sync out/ s3://gympt-fe-deploy-337112169365/ --delete

# 2. CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E14Z61F5I2E9ZM \
  --paths "/*"

# 3. 배포 확인 (5-10분 후)
curl -I https://your-domain.com
```

### 🔧 백엔드 API 응답 없음

```bash
# 1. Pod 상태 확인
kubectl get pods -n gympt-dev

# 2. 로그 확인 (Pod 이름은 위에서 확인)
kubectl logs backend-api-xxxxxx-xxxxx -n gympt-dev

# 3. Pod 재시작
kubectl rollout restart deployment backend-api -n gympt-dev

# 4. API 테스트
kubectl get ingress -n gympt-dev
# ALB URL 복사 후
curl http://<ALB-URL>/actuator/health
```

### 📊 ArgoCD에서 Out of Sync

```bash
# 1. ArgoCD UI 접속
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 브라우저: https://localhost:8080

# 2. 비밀번호 확인
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d

# 3. 수동 Sync
# UI에서 각 애플리케이션 선택 → SYNC 버튼 클릭
```

---

## 🔍 상세 점검 가이드

자세한 내용은 다음 문서를 참조하세요:
- [전체 시스템 헬스 체크 가이드](./SYSTEM_HEALTH_CHECK.md)

---

## 📞 체크리스트

시스템이 정상 동작하려면 다음이 모두 ✅ 여야 합니다:

### Infrastructure
- [ ] AWS 계정 로그인 가능
- [ ] EKS 클러스터 접근 가능 (`kubectl cluster-info`)
- [ ] S3 버킷에 frontend 파일 존재
- [ ] CloudFront Distribution Deployed 상태

### Backend Services
- [ ] backend-api Pod: Running (2/2)
- [ ] agent-service Pod: Running (2/2)
- [ ] posture-analysis-service Pod: Running (2/2)
- [ ] RDS Database: Available

### GitOps
- [ ] ArgoCD: 모든 앱 Synced
- [ ] ArgoCD: 모든 앱 Healthy

### Networking
- [ ] Ingress ALB 생성됨
- [ ] DNS 레코드가 ALB/CloudFront 가리킴
- [ ] API Health Check: 200 OK

---

## 🛠️ 유용한 명령어

### Kubernetes 기본

```bash
# 현재 컨텍스트 확인
kubectl config current-context

# 네임스페이스 전환
kubectl config set-context --current --namespace=gympt-dev

# 모든 리소스 확인
kubectl get all -n gympt-dev

# Pod 로그 실시간 보기
kubectl logs -f <pod-name> -n gympt-dev

# Pod 내부 접속
kubectl exec -it <pod-name> -n gympt-dev -- /bin/bash

# 리소스 삭제 후 재생성
kubectl delete pod <pod-name> -n gympt-dev
kubectl rollout restart deployment <deployment-name> -n gympt-dev
```

### AWS CLI

```bash
# S3 버킷 파일 목록
aws s3 ls s3://gympt-fe-deploy-337112169365/ --recursive

# S3 동기화
aws s3 sync ./local-folder s3://bucket-name/ --delete

# CloudFront 무효화
aws cloudfront create-invalidation \
  --distribution-id E14Z61F5I2E9ZM \
  --paths "/*"

# RDS 엔드포인트 확인
aws rds describe-db-instances \
  --db-instance-identifier gympt-dev-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# EKS 클러스터 정보
aws eks describe-cluster --name gympt-dev \
  --query 'cluster.{Name:name,Status:status,Endpoint:endpoint}'
```

### ArgoCD CLI

```bash
# 설치 (Mac)
brew install argocd

# 설치 (Linux)
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# 로그인
argocd login localhost:8080

# 앱 목록
argocd app list

# 앱 Sync
argocd app sync backend-api
argocd app sync agent-service
argocd app sync posture-analysis-service

# 앱 상태 확인
argocd app get backend-api
```

---

## 📈 모니터링

### CloudWatch 로그 확인

```bash
# EKS 클러스터 로그
https://console.aws.amazon.com/cloudwatch/home?region=ap-northeast-2#logsV2:log-groups

# ALB 액세스 로그
S3 버킷: gympt-dev-alb-logs-337112169365
```

### Prometheus & Grafana (설치된 경우)

```bash
# Prometheus port-forward
kubectl port-forward -n monitoring svc/prometheus-server 9090:80

# Grafana port-forward  
kubectl port-forward -n monitoring svc/grafana 3000:80

# 브라우저
http://localhost:9090  # Prometheus
http://localhost:3000  # Grafana
```

---

## 🆘 긴급 문제 해결

### 모든 서비스 다운

```bash
# 1. 클러스터 전체 상태 확인
kubectl get nodes
kubectl get pods --all-namespaces

# 2. 이벤트 확인
kubectl get events --all-namespaces --sort-by='.lastTimestamp'

# 3. 네임스페이스 재시작
kubectl delete pods --all -n gympt-dev
# ArgoCD가 자동으로 재생성함
```

### Database 연결 불가

```bash
# 1. RDS 보안 그룹 확인
# EC2 Console → Security Groups → RDS SG
# Inbound: 5432 from EKS Node SG

# 2. RDS 상태 확인
aws rds describe-db-instances \
  --db-instance-identifier gympt-dev-postgres

# 3. Pod에서 연결 테스트
kubectl run psql-test --rm -it --image=postgres:15 -n gympt-dev -- \
  psql -h <RDS-ENDPOINT> -U gympt_user -d gympt_db
```

### GitHub Actions 계속 실패

```bash
# 1. Secrets 확인
# GitHub → Settings → Secrets and variables → Actions

필요한 Secrets:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- GITOPS_PAT (Personal Access Token)

# 2. 로컬에서 수동 배포 테스트
cd backend-api
./gradlew build -x test
docker build -t test:latest .

# 3. 워크플로우 재실행
# GitHub Actions → 실패한 워크플로우 → Re-run jobs
```

---

## 📚 추가 리소스

- [시스템 아키텍처](../docs/architecture.md)
- [배포 가이드](../docs/deployment.md)
- [트러블슈팅](./SYSTEM_HEALTH_CHECK.md)
- [GitHub Actions 워크플로우](../.github/workflows/)

---

## 💬 도움이 필요한 경우

1. **로그 수집**
   ```bash
   # Pod 로그
   kubectl logs <pod-name> -n gympt-dev > pod-logs.txt
   
   # 전체 리소스 상태
   kubectl get all -n gympt-dev -o yaml > resources.yaml
   
   # 이벤트
   kubectl get events -n gympt-dev > events.txt
   ```

2. **스크린샷 준비**
   - GitHub Actions 실패 화면
   - ArgoCD UI
   - AWS Console (S3, CloudFront, RDS)

3. **오류 메시지와 함께 질문**

---

**문제가 해결되지 않으면 구체적인 오류 메시지를 알려주세요!**
