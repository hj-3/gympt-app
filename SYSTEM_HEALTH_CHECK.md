# GYMPT 시스템 상태 점검 가이드

## 🎯 목적
프론트엔드 접속 불가 및 전체 시스템 동작 여부 확인

---

## 📋 체크리스트

### ✅ 1. GitHub Actions 빌드 상태 확인

```bash
# 브라우저에서 확인
https://github.com/hj-3/gympt-app/actions

# 확인 항목
- [ ] Frontend Deploy: 최근 빌드 성공 (초록색 체크)
- [ ] Backend API CI/CD: 최근 빌드 성공
- [ ] Agent Service CI/CD: 최근 빌드 성공
- [ ] Posture Analysis Service CI/CD: 최근 빌드 성공
```

**❌ 실패 시:** 워크플로우 로그 확인 후 오류 수정

---

### ✅ 2. AWS 인프라 상태 확인

#### 2.1 S3 & CloudFront (프론트엔드)

```bash
# 1. AWS Console 로그인
https://console.aws.amazon.com/

# 2. S3 버킷 확인
리전: ap-northeast-2 (서울)
버킷 이름:
- Prod: gympt-fe-deploy-337112169365
- Dev: gympt-dev-frontend-337112169365

확인 항목:
- [ ] 버킷이 존재하는가?
- [ ] index.html 파일이 있는가?
- [ ] _next/static/ 폴더가 있는가?
- [ ] 최종 수정 날짜가 최근인가?

# 3. S3에서 직접 접속 테스트
S3 콘솔 → 버킷 → 속성 → 정적 웹사이트 호스팅
URL: http://gympt-fe-deploy-337112169365.s3-website.ap-northeast-2.amazonaws.com
```

**⚠️ 버킷이 없거나 파일이 없다면:**
```bash
# Terraform으로 인프라 생성
cd gympt-infra
terraform init
terraform plan
terraform apply
```

#### 2.2 CloudFront (CDN)

```bash
# CloudFront 콘솔 확인
https://console.aws.amazon.com/cloudfront/

확인 항목:
Distribution ID: E14Z61F5I2E9ZM (Prod)

- [ ] Status: Enabled
- [ ] State: Deployed (배포 완료)
- [ ] Origin: gympt-fe-deploy-337112169365.s3.ap-northeast-2.amazonaws.com
- [ ] Alternate Domain Names (CNAME): 도메인 설정 확인

# CloudFront URL로 직접 접속 테스트
https://xxxxxx.cloudfront.net
```

**❌ Distribution이 없다면:**
```bash
# Terraform에서 CloudFront 리소스 확인
cd gympt-infra/environments/prod
grep -r "cloudfront" *.tf
terraform apply
```

#### 2.3 Route 53 (DNS)

```bash
# Route 53 콘솔 확인
https://console.aws.amazon.com/route53/

호스팅 영역 확인:
- [ ] 도메인 호스팅 영역 존재
- [ ] A 레코드 또는 CNAME이 CloudFront를 가리킴

# DNS 확인
nslookup your-domain.com
dig your-domain.com

# 예상 결과
# CNAME → xxxxxx.cloudfront.net
# 또는
# A Record (Alias) → CloudFront Distribution
```

---

### ✅ 3. EKS 백엔드 서비스 확인

#### 3.1 EKS 클러스터 접속

```bash
# AWS Console에서 EKS 확인
리전: ap-northeast-2
클러스터 이름: gympt-dev 또는 gympt-prod

# kubectl 설정
aws eks update-kubeconfig --region ap-northeast-2 --name gympt-dev
kubectl config current-context

# 클러스터 노드 확인
kubectl get nodes
# 예상: 3개 노드 (각 AZ에 1개씩)
```

#### 3.2 Pod 상태 확인

```bash
# 모든 네임스페이스의 Pod 확인
kubectl get pods --all-namespaces

# 각 서비스별 Pod 확인
kubectl get pods -n gympt-dev

# 확인 항목
- [ ] backend-api: Running (2 replicas)
- [ ] agent-service: Running (2 replicas)
- [ ] posture-analysis-service: Running (2 replicas)

# Pod 로그 확인 (문제가 있는 경우)
kubectl logs -f <pod-name> -n gympt-dev
kubectl describe pod <pod-name> -n gympt-dev
```

**❌ Pod가 CrashLoopBackOff 상태라면:**
```bash
# 로그 확인
kubectl logs <pod-name> -n gympt-dev --previous

# 일반적인 원인
1. 환경 변수 누락 (DB 연결 정보, AWS 자격 증명)
2. ConfigMap/Secret 누락
3. 이미지 태그 오류
4. Health check 실패
```

#### 3.3 Service & Ingress 확인

```bash
# Service 확인
kubectl get svc -n gympt-dev

# Ingress 확인
kubectl get ingress -n gympt-dev

# Ingress 상세 정보
kubectl describe ingress backend-api-ingress -n gympt-dev

# ALB (Application Load Balancer) 주소 확인
ALB_URL=$(kubectl get ingress backend-api-ingress -n gympt-dev -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "ALB URL: $ALB_URL"

# API 엔드포인트 테스트
curl https://api.your-domain.com/actuator/health
curl https://api-dev.your-domain.com/actuator/health
```

---

### ✅ 4. RDS 데이터베이스 확인

```bash
# RDS 콘솔 확인
https://console.aws.amazon.com/rds/

확인 항목:
- [ ] 인스턴스 이름: gympt-dev-postgres 또는 gympt-prod-postgres
- [ ] Status: Available
- [ ] 엔드포인트: xxxxx.rds.amazonaws.com

# 데이터베이스 연결 테스트 (EKS Pod에서)
kubectl run -it --rm psql-test --image=postgres:15 --restart=Never -n gympt-dev -- \
  psql -h <RDS_ENDPOINT> -U gympt_user -d gympt_db

# 연결 성공하면
\dt  # 테이블 목록 확인
\q   # 종료
```

---

### ✅ 5. ArgoCD (GitOps) 확인

```bash
# ArgoCD UI 접속
# Kubernetes에서 ArgoCD 서비스 확인
kubectl get svc -n argocd

# Port-forward로 로컬에서 접속
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 브라우저에서
https://localhost:8080

# 로그인
Username: admin
Password: (초기 비밀번호 확인)
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d

# ArgoCD에서 확인
- [ ] backend-api 앱: Synced + Healthy
- [ ] agent-service 앱: Synced + Healthy
- [ ] posture-analysis-service 앱: Synced + Healthy
```

**❌ Out of Sync 또는 Degraded 상태라면:**
```bash
# ArgoCD에서 수동 Sync
argocd app sync backend-api
argocd app sync agent-service
argocd app sync posture-analysis-service

# 또는 UI에서 "SYNC" 버튼 클릭
```

---

## 🔧 트러블슈팅 시나리오

### 시나리오 1: 프론트엔드 접속 시 404 Not Found

**원인 진단:**
```bash
# 1. S3 버킷 확인
aws s3 ls s3://gympt-fe-deploy-337112169365/

# 2. CloudFront 캐시 확인
# CloudFront 콘솔 → Invalidations → Create Invalidation
경로: /*

# 3. DNS 전파 확인
nslookup your-domain.com
# CloudFront URL을 가리키는지 확인
```

**해결 방법:**
```bash
# Frontend 재배포
cd gympt-app
git push origin main  # 변경 사항이 있다면

# 또는 수동 배포
cd frontend
npm run build:prod
aws s3 sync out/ s3://gympt-fe-deploy-337112169365/ --delete
aws cloudfront create-invalidation --distribution-id E14Z61F5I2E9ZM --paths "/*"
```

---

### 시나리오 2: 프론트엔드는 보이지만 API 호출 실패

**증상:**
- 프론트엔드 페이지는 로드됨
- 로그인/데이터 로딩 실패
- 브라우저 콘솔: `ERR_CONNECTION_REFUSED` 또는 CORS 오류

**원인 진단:**
```bash
# 1. API 엔드포인트 테스트
curl -v https://api.your-domain.com/actuator/health

# 2. Backend Pod 상태 확인
kubectl get pods -n gympt-dev | grep backend-api
kubectl logs <backend-api-pod> -n gympt-dev

# 3. Ingress 확인
kubectl get ingress -n gympt-dev
kubectl describe ingress backend-api-ingress -n gympt-dev
```

**해결 방법:**
```bash
# 1. 환경 변수 확인 (Frontend)
# frontend/.env.production 또는 next.config.js
NEXT_PUBLIC_API_URL=https://api.your-domain.com

# 2. CORS 설정 확인 (Backend)
# backend-api/src/main/java/com/gympt/backend/config/WebConfig.java
# 허용된 Origin에 프론트엔드 도메인 포함 확인

# 3. ALB Security Group 확인
# EC2 → Security Groups → ALB SG
# Inbound: 443 (HTTPS) from 0.0.0.0/0 허용
```

---

### 시나리오 3: 모든 서비스가 CrashLoopBackOff

**원인 진단:**
```bash
# Pod 로그 확인
kubectl logs <pod-name> -n gympt-dev --previous

# 일반적인 오류
1. "Connection refused" → DB 연결 실패
2. "Access Denied" → AWS 권한 문제
3. "Port already in use" → 포트 충돌
```

**해결 방법:**
```bash
# 1. ConfigMap 확인
kubectl get configmap -n gympt-dev
kubectl describe configmap backend-api-config -n gympt-dev

# 2. Secret 확인
kubectl get secret -n gympt-dev
kubectl describe secret backend-api-secret -n gympt-dev

# 3. 환경 변수 디버깅
kubectl exec -it <pod-name> -n gympt-dev -- env | grep DB

# 4. 재시작
kubectl rollout restart deployment backend-api -n gympt-dev
```

---

## 📊 완전한 시스템 상태 점검 스크립트

아래 스크립트를 실행하여 전체 시스템 상태를 한 번에 확인하세요:

```bash
#!/bin/bash
# system-health-check.sh

echo "🔍 GYMPT System Health Check"
echo "================================"

# 1. Kubernetes Cluster
echo ""
echo "1️⃣ EKS Cluster Connection"
kubectl cluster-info
echo ""

# 2. Namespaces
echo "2️⃣ Namespaces"
kubectl get ns | grep gympt
echo ""

# 3. Pods
echo "3️⃣ Pod Status"
kubectl get pods -n gympt-dev -o wide
echo ""

# 4. Services
echo "4️⃣ Services"
kubectl get svc -n gympt-dev
echo ""

# 5. Ingress
echo "5️⃣ Ingress & ALB"
kubectl get ingress -n gympt-dev
echo ""

# 6. API Health Check
echo "6️⃣ API Health Check"
ALB_URL=$(kubectl get ingress backend-api-ingress -n gympt-dev -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -s http://${ALB_URL}/actuator/health | jq .
echo ""

# 7. ArgoCD Apps
echo "7️⃣ ArgoCD Applications"
kubectl get applications -n argocd
echo ""

# 8. Recent Deployments
echo "8️⃣ Recent Deployments"
kubectl get deployments -n gympt-dev
echo ""

echo "================================"
echo "✅ Health Check Complete"
```

**실행 방법:**
```bash
chmod +x system-health-check.sh
./system-health-check.sh
```

---

## 🌐 도메인별 접속 테스트

### Production
```bash
# Frontend
https://your-domain.com

# Backend API
https://api.your-domain.com/actuator/health
https://api.your-domain.com/api/v1/auth/login

# WebSocket (운동 세션)
wss://api.your-domain.com/ws/sessions/{sessionId}
```

### Development
```bash
# Frontend
https://dev.your-domain.com

# Backend API  
https://api-dev.your-domain.com/actuator/health

# WebSocket
wss://api-dev.your-domain.com/ws/sessions/{sessionId}
```

---

## 📞 다음 단계

### 프론트엔드가 안 보이는 경우
1. ✅ S3 버킷에 파일이 있는지 확인
2. ✅ CloudFront Distribution이 Deployed 상태인지 확인
3. ✅ Route 53 DNS 레코드가 CloudFront를 가리키는지 확인
4. ✅ GitHub Actions Frontend Deploy 워크플로우 로그 확인

### API 호출이 실패하는 경우
1. ✅ Backend Pod가 Running 상태인지 확인
2. ✅ Service와 Ingress가 정상인지 확인
3. ✅ RDS 데이터베이스 연결 가능한지 확인
4. ✅ CORS 설정 확인

### 추가 지원이 필요한 경우
```bash
# 로그 수집
kubectl logs <pod-name> -n gympt-dev > pod-logs.txt
kubectl describe pod <pod-name> -n gympt-dev > pod-describe.txt

# ArgoCD 상태 확인
kubectl get applications -n argocd -o yaml > argocd-apps.yaml

# 현재 설정 백업
kubectl get all -n gympt-dev -o yaml > gympt-dev-resources.yaml
```

---

## ✅ 정상 동작 확인 체크리스트

시스템이 완전히 동작하려면 다음이 모두 ✅ 상태여야 합니다:

- [ ] Frontend: CloudFront에서 index.html 로드 성공
- [ ] Backend API: Health check 200 OK
- [ ] Agent Service: Health check 200 OK  
- [ ] Posture Analysis: Health check 200 OK
- [ ] Database: 연결 성공
- [ ] ArgoCD: 모든 앱 Synced + Healthy
- [ ] DNS: 도메인이 CloudFront/ALB로 정상 라우팅

---

**문제가 지속되면 구체적인 오류 메시지와 함께 질문해주세요!**
