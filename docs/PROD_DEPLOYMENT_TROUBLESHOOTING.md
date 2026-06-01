# GYMPT Prod 배포 트러블슈팅 기록

> 기간: 2026-05-29 ~ 2026-06-01  
> 환경: AWS EKS (ap-northeast-2), gympt-prod 네임스페이스  
> 작업 범위: 3개 저장소 전체 분석 및 prod 서비스 기동

---

## 목차

1. [전체 이슈 분석 (2026-05-29)](#1-전체-이슈-분석)
2. [WAF 모듈 삭제](#2-waf-모듈-삭제)
3. [gympt-app 코드 수정 (CORS·Bedrock Mock·하드코딩)](#3-gympt-app-코드-수정)
4. [RDS 비밀번호 InvalidParameterValue 오류](#4-rds-비밀번호-invalidparametervalue-오류)
5. [backend-api CrashLoopBackOff — DB 인증 실패](#5-backend-api-crashloopbackoff--db-인증-실패)
6. [Karpenter 노드 프로비저닝 실패 — 다른 VPC 태그 혼재](#6-karpenter-노드-프로비저닝-실패--다른-vpc-태그-혼재)
7. [Karpenter 노드 DNS 불통 — 노드 간 SG 격리](#7-karpenter-노드-dns-불통--노드-간-sg-격리)
8. [backend-api CrashLoopBackOff — Hibernate 스키마 불일치](#8-backend-api-crashloopbackoff--hibernate-스키마-불일치)
9. [코드 하드코딩 일괄 수정](#9-코드-하드코딩-일괄-수정)
10. [posture-analysis-service Pending — GPU 노드 그룹 0대](#10-posture-analysis-service-pending--gpu-노드-그룹-0대)
11. [Ingress 중복 — ALB 미프로비저닝으로 API 외부 접근 불가](#11-ingress-중복--alb-미프로비저닝으로-api-외부-접근-불가)
12. [agent-service·remediation-worker ExternalSecret 누락](#12-agent-serviceremediation-worker-externalsecret-누락)
13. [현재 상태 및 남은 작업](#13-현재-상태-및-남은-작업)

---

## 1. 전체 이슈 분석

**일자:** 2026-05-29

3개 저장소(`gympt-app`, `gympt-gitops`, `gympt-infra`)를 전체 분석하여 Critical/High 이슈를 식별했다.

### gympt-app 주요 이슈

| 심각도 | 파일 | 내용 |
|--------|------|------|
| Critical | `agent-service/app/config.py` | `enable_bedrock_mock: bool = True` — Prod에서 Mock 활성화 |
| Critical | `agent-service/app/clients/sqs_client.py:111` | `"timestamp": settings.app_env` — 환경명이 timestamp에 저장되는 버그 |
| Critical | `backend-api/application.yml:68` | Cognito `issuer-uri` 플레이스홀더 — 환경변수 누락 시 JWT 전체 실패 |
| Critical | 모든 Python 서비스 | `allow_origins=["*"]` CORS 완전 개방 |
| Critical | `.github/workflows/backend-api-ci.yml` | `./gradlew clean build -x test` — 테스트 건너뜀 |
| High | `agent-service/.../backend_client.py` | 재시도 로직 미흡 (503, 429 미처리) |
| High | `agent-service/.../cache_service.py:175` | Redis `KEYS` 명령 O(N) 스캔 |
| High | `backend-api/SecurityConfig.java` | `/actuator/prometheus` 공개 노출 |
| High | `posture-analysis-service/app/main.py` | WebSocket 리소스 정리 불명확, 메모리 누수 위험 |
| High | `report-service/src/config/settings.py` | S3 버킷명 하드코딩 |

### gympt-gitops 주요 이슈

| 심각도 | 파일 | 내용 |
|--------|------|------|
| Critical | `charts/backend-api/values-prod.yaml` | `externalSecrets.enabled: false` — Prod Secret 평문 저장 |
| Critical | `platform/external-secrets/external-secret-backend-api.yaml:47` | `key: gympt/dev/backend-api` dev 경로 하드코딩 |
| High | `argocd/projects/gympt-platform.yaml:11` | `sourceRepos: ['*']` 전체 저장소 허용 |
| High | `argocd/applications/prod/agent-service.yaml:24-26` | Prod `prune: true, selfHeal: true` — 자동 삭제 위험 |
| High | `platform/network-policies/posture-analysis-netpol.yaml:95-104` | 존재하지 않는 `ml-models` 네임스페이스 참조 |

### gympt-infra 주요 이슈

| 심각도 | 파일 | 내용 |
|--------|------|------|
| Critical | `terraform/environments/dev/main.tf:113` | `master_password = "changeme123"` 하드코딩 |
| Critical | `terraform/modules/eks/variables.tf:27-36` | EKS 공개 API `0.0.0.0/0` 전 세계 노출 |
| High | `terraform/modules/iam/main.tf:91` | AWS Account ID `337112169365` 하드코딩 |
| High | `terraform/modules/rds/main.tf:32-37` | RDS Egress 전체 개방 (`0.0.0.0/0`) |
| High | `terraform/modules/elasticache/main.tf:32-37` | ElastiCache Egress 전체 개방 |
| High | `terraform/modules/karpenter/main.tf:52` | IAM `Resource: "*"` 과도한 권한 |
| High | `terraform/modules/eks/main.tf:241` | GPU 노드 k8s 버전 1.32 vs 일반 노드 1.35 불일치 |

---

## 2. WAF 모듈 삭제

**일자:** 2026-05-29  
**저장소:** gympt-infra

### 증상
`terraform/modules/waf/` 모듈이 존재하지만 CloudFront에서 직접 WAF를 붙이는 방식으로 변경 결정.

### 조치
- `terraform/modules/waf/` 디렉토리 전체 삭제
- `terraform/environments/dev/main.tf`, `prod/main.tf`에서 WAF 모듈 참조 제거

---

## 3. gympt-app 코드 수정

**일자:** 2026-05-29 ~ 2026-05-31  
**커밋:** `c95ae28 fix: compatibility issues, hardcoded values, CORS, Bedrock mock`

### 수정 내용

#### 3-1. Bedrock Mock 기본값 수정
```python
# before: agent-service/app/config.py
enable_bedrock_mock: bool = True

# after
enable_bedrock_mock: bool = False
```

**원인:** 기본값이 `True`이면 환경변수 미설정 시 Prod에서 Mock으로 동작.  
**수정:** 기본값을 `False`로 변경, `ENABLE_BEDROCK_MOCK=true` 명시 설정 시에만 Mock 활성화.

#### 3-2. CORS 수정
```python
# before (모든 Python 서비스)
allow_origins=["*"]

# after
allow_origins=settings.allowed_origins  # 환경변수로 도메인 지정
```

#### 3-3. SQS Timestamp 버그 수정
```python
# before: agent-service/app/clients/sqs_client.py:111
"timestamp": settings.app_env   # 버그: 환경명("prod")이 들어감

# after
"timestamp": datetime.utcnow().isoformat()
```

---

## 4. RDS 비밀번호 InvalidParameterValue 오류

**일자:** 2026-06-01  
**저장소:** gympt-app (scripts)

### 증상
```
aws rds modify-db-instance ... --master-user-password "wP2JG8SpigzBkqK5qz2/PiYUAmcfLCP82VU9nsYCnpQ="

An error occurred (InvalidParameterValue): The parameter MasterUserPassword is not a valid password.
Only printable ASCII characters besides '/', '@', '"', ' ' may be used.
```

### 원인
RDS 비밀번호에 금지 문자 포함:
- `/` → RDS 금지 문자
- `=` → Base64 padding 문자로 허용되지 않음

### 조치
```bash
# RDS 허용 문자로만 구성된 비밀번호 생성
< /dev/urandom tr -dc 'A-Za-z0-9!#$%^&*()_+[]{}|;:,.<>?' | head -c 32
# → dVz+.m&R6>Oc26;}+sf|[J4s8a*n6J*d

aws rds modify-db-instance \
  --db-instance-identifier gympt-prod-postgres \
  --master-user-password "dVz+.m&R6>Oc26;}+sf|[J4s8a*n6J*d" \
  --apply-immediately \
  --region ap-northeast-2
```

### 학습 포인트
RDS 비밀번호 생성 시 `/`, `@`, `"`, 공백을 반드시 제외할 것.  
`openssl rand` 또는 `tr -dc` 기반 생성기 사용 권장.

---

## 5. backend-api CrashLoopBackOff — DB 인증 실패

**일자:** 2026-06-01

### 증상
```
kubectl logs backend-api-prod-xxx -n gympt-prod
→ Caused by: FATAL: password authentication failed for user "gymptadmin"
```

### 원인
AWS Secrets Manager(`gympt/prod/database`)의 값이 3가지 모두 잘못됨:

| 필드 | Secrets Manager 값 | 실제 RDS 값 |
|------|-------------------|------------|
| `username` | `gympt_admin` | `gymptadmin` (언더바 없음) |
| `password` | 이전 비밀번호 (4번에서 변경됨) | 새 비밀번호 |
| `host` | `gympt-prod-db.cluster-xxxxx...` (플레이스홀더) | `gympt-prod-postgres.cpuskg4g6hoy.ap-northeast-2.rds.amazonaws.com` |

### 조치

```bash
# 1. Secrets Manager 업데이트
aws secretsmanager update-secret \
  --secret-id gympt/prod/database \
  --region ap-northeast-2 \
  --secret-string '{
    "username": "gymptadmin",
    "password": "dVz+.m&R6>Oc26;}+sf|[J4s8a*n6J*d",
    "host": "gympt-prod-postgres.cpuskg4g6hoy.ap-northeast-2.rds.amazonaws.com",
    "port": "5432",
    "database": "gympt"
  }'

# 2. ExternalSecret 강제 갱신
kubectl annotate externalsecret backend-api-prod-secrets \
  -n gympt-prod force-sync=$(date +%s) --overwrite

# 3. Deployment 재시작
kubectl rollout restart deployment/backend-api-prod -n gympt-prod
```

### 학습 포인트
- RDS 마스터 사용자명은 Terraform 모듈에 `master_username` 값이 정의되어 있으므로 반드시 동일하게 맞출 것.
- Secrets Manager에 플레이스홀더 값이 남아있는지 초기 설정 시 반드시 검증.
- 비밀번호 변경 시: RDS 변경 → Secrets Manager 업데이트 → ExternalSecret 강제 동기화 순서로 진행.

---

## 6. Karpenter 노드 프로비저닝 실패 — 다른 VPC 태그 혼재

**일자:** 2026-06-01

### 증상
backend-api Pod가 `Pending` 상태 (CPU 부족), Karpenter가 새 노드를 프로비저닝하지 못함.

```bash
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter | grep ERROR
→ Security group sg-0c79421bbf2625bce and subnet subnet-052c2c7ea25467e55 belong to different networks.
  (aws-error-code=UnfulfillableCapacity)
```

### 원인
Karpenter EC2NodeClass는 `karpenter.sh/discovery: gympt-prod-eks` 태그로 SG와 Subnet을 자동 탐색하는데, **이전 VPC의 리소스에 해당 태그가 그대로 남아있어** 다른 VPC의 SG + Subnet 조합이 발생함.

```
현재 VPC (vpc-0e7d2db156f48515d):
  SG: sg-0c79421bbf2625bce ✓
  Subnet: subnet-09bc64717bafd6550, subnet-0c69317e659bde74d ✓

이전 VPC (vpc-065db1d18f52f964e) — 태그가 남아있어 혼재됨:
  SG: sg-07dd6c7d06fe338a3 ✗
  Subnet: subnet-0de1a8a75f20b9927, subnet-052c2c7ea25467e55 ✗
```

### 조치

```bash
# 이전 VPC 리소스에서 Karpenter 태그 제거
aws ec2 delete-tags \
  --resources subnet-0de1a8a75f20b9927 subnet-052c2c7ea25467e55 \
  --tags Key=karpenter.sh/discovery \
  --region ap-northeast-2

aws ec2 delete-tags \
  --resources sg-07dd6c7d06fe338a3 \
  --tags Key=karpenter.sh/discovery \
  --region ap-northeast-2

# 실패한 NodeClaim 삭제 (자동 재시도됨)
kubectl delete nodeclaim general-7rdt8
```

### 확인

```bash
aws ec2 describe-security-groups \
  --filters "Name=tag:karpenter.sh/discovery,Values=gympt-prod-eks" \
  --query 'SecurityGroups[*].{ID:GroupId,VPC:VpcId}' --output table

aws ec2 describe-subnets \
  --filters "Name=tag:karpenter.sh/discovery,Values=gympt-prod-eks" \
  --query 'Subnets[*].{ID:SubnetId,VPC:VpcId,AZ:AvailabilityZone}' --output table
# → 모든 리소스가 동일 VPC로 표시되어야 함
```

### 학습 포인트
- VPC를 재생성하거나 환경을 재구성한 경우, 이전 VPC의 리소스에 남은 Karpenter 태그를 반드시 제거.
- 진단 시 `kubectl logs -n karpenter` 에서 `UnfulfillableCapacity` 에러와 함께 SG/Subnet ID가 출력되므로 해당 ID의 VPC를 확인.

---

## 7. Karpenter 노드 DNS 불통 — 노드 간 SG 격리

**일자:** 2026-06-01

### 증상
6번에서 Karpenter 노드가 생성됐지만, 해당 노드에 올라간 Pod에서 DNS 조회 실패:

```
kubectl logs backend-api-prod-6b9c9b4d7b-qvvsd -n gympt-prod
→ java.net.UnknownHostException: gympt-prod-postgres.cpuskg4g6hoy.ap-northeast-2.rds.amazonaws.com

# DNS 직접 테스트
kubectl run dns-test --image=busybox --restart=Never -n gympt-prod \
  --overrides='{"spec":{"nodeName":"ip-10-1-63-224..."}}'
  --command -- nslookup gympt-prod-postgres...
→ ;; connection timed out; no servers could be reached
```

### 원인
EKS에는 두 종류의 보안 그룹이 존재:

| 종류 | SG ID | 사용 노드 |
|------|-------|----------|
| AWS 자동 생성 클러스터 SG | `sg-0a4a12081fa6d25db` (`eks-cluster-sg-*`) | 관리형 노드 그룹 |
| Terraform 생성 노드 SG | `sg-0c79421bbf2625bce` (`gympt-prod-eks-node-*`) | Karpenter 프로비저닝 노드 |

두 SG 사이에 **상호 인바운드 허용 규칙이 없어서** Karpenter 노드 → 관리형 노드의 CoreDNS Pod(포트 53) 통신이 차단됨.

### 조치

```bash
# 관리형 노드 SG → Karpenter 노드 SG 인바운드 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-0a4a12081fa6d25db \
  --protocol -1 \
  --source-group sg-0c79421bbf2625bce \
  --region ap-northeast-2

# Karpenter 노드 SG → 관리형 노드 SG 인바운드 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-0c79421bbf2625bce \
  --protocol -1 \
  --source-group sg-0a4a12081fa6d25db \
  --region ap-northeast-2
```

#### Terraform 영속화 (terraform/modules/eks/main.tf에 추가)

```hcl
resource "aws_security_group_rule" "node_ingress_from_cluster_sg" {
  description              = "Allow traffic from EKS managed nodes (cluster SG) to Karpenter nodes"
  type                     = "ingress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.node.id
  source_security_group_id = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

resource "aws_security_group_rule" "cluster_sg_ingress_from_node" {
  description              = "Allow traffic from Karpenter nodes to EKS managed nodes (cluster SG)"
  type                     = "ingress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  security_group_id        = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  source_security_group_id = aws_security_group.node.id
}
```

### 확인

```bash
kubectl run dns-test --image=nicolaka/netshoot --restart=Never -n gympt-prod \
  --overrides='{"spec":{"nodeName":"<karpenter-node>"}}' \
  --command -- nslookup gympt-prod-postgres.cpuskg4g6hoy.ap-northeast-2.rds.amazonaws.com
# → Address: 10.1.84.24 (성공)
```

### 학습 포인트
- EKS에서 Karpenter와 관리형 노드 그룹을 **혼용**하면 SG가 달라지므로 반드시 크로스 SG 룰을 설정.
- `aws_eks_cluster.main.vpc_config[0].cluster_security_group_id`로 자동 생성 클러스터 SG를 참조 가능.
- CoreDNS가 관리형 노드에 있고 Karpenter 노드에서 DNS가 안 된다면 이 이슈일 가능성이 높음.

---

## 8. backend-api CrashLoopBackOff — Hibernate 스키마 불일치

**일자:** 2026-06-01

### 증상
DNS·DB 연결은 성공했지만 Spring Boot 기동 실패:

```
Caused by: org.hibernate.tool.schema.spi.SchemaManagementException:
  Schema-validation: missing column [body_fat] in table [body_profiles]
```

### 원인
Flyway 마이그레이션 V1의 `body_profiles` 테이블 컬럼명이 JPA 엔티티(`BodyProfile.java`)와 불일치:

| Flyway V1 컬럼명 | JPA 엔티티 매핑 컬럼명 | 불일치 여부 |
|-----------------|----------------------|-----------|
| `height_cm INTEGER` | `height DECIMAL(5,2)` | ✗ 이름·타입 불일치 |
| `weight_kg DECIMAL(5,2)` | `weight DECIMAL(5,2)` | ✗ 이름 불일치 |
| `body_fat_percentage DECIMAL(4,2)` | `body_fat DECIMAL(5,2)` | ✗ 이름·precision 불일치 |
| _(없음)_ | `muscle_mass DECIMAL(5,2)` | ✗ 컬럼 누락 |
| _(없음)_ | `posture_type VARCHAR(50)` | ✗ 컬럼 누락 |
| _(없음)_ | `measurement_date DATE NOT NULL` | ✗ 컬럼 누락 |

### 조치
`V4__Fix_body_profiles_schema.sql` 마이그레이션 파일 생성:

```sql
-- backend-api/src/main/resources/db/migration/V4__Fix_body_profiles_schema.sql

ALTER TABLE body_profiles RENAME COLUMN height_cm TO height;
ALTER TABLE body_profiles ALTER COLUMN height TYPE DECIMAL(5,2) USING height::DECIMAL(5,2);
ALTER TABLE body_profiles ALTER COLUMN height SET NOT NULL;

ALTER TABLE body_profiles RENAME COLUMN weight_kg TO weight;
ALTER TABLE body_profiles ALTER COLUMN weight SET NOT NULL;

ALTER TABLE body_profiles RENAME COLUMN body_fat_percentage TO body_fat;
ALTER TABLE body_profiles ALTER COLUMN body_fat TYPE DECIMAL(5,2);

ALTER TABLE body_profiles ADD COLUMN IF NOT EXISTS muscle_mass DECIMAL(5,2);
ALTER TABLE body_profiles ADD COLUMN IF NOT EXISTS posture_type VARCHAR(50);
ALTER TABLE body_profiles ADD COLUMN IF NOT EXISTS measurement_date DATE NOT NULL DEFAULT CURRENT_DATE;

CREATE INDEX IF NOT EXISTS idx_body_profile_user_date ON body_profiles(user_id, measurement_date);
```

### 확인 방법
```bash
# 새 이미지 배포 후 로그 확인
kubectl logs -f deployment/backend-api-prod -n gympt-prod | grep -E "Started|ERROR"
# → Started GymptBackendApplication 출력 시 성공
```

### 학습 포인트
- JPA 엔티티의 `@Column(name = "...")` 어노테이션과 Flyway SQL의 컬럼명을 항상 일치시킬 것.
- 엔티티를 먼저 작성하고 SQL을 나중에 작성하면 이런 불일치가 발생하기 쉬움. DB First 또는 Entity First 중 하나를 팀에서 통일.
- Hibernate `spring.jpa.hibernate.ddl-auto=validate`는 기동 시 전체 스키마 검사를 수행하므로 누락 컬럼을 빠르게 감지할 수 있음 (Prod에서 권장).

---

## 9. 코드 하드코딩 일괄 수정

**일자:** 2026-06-01  
**저장소:** gympt-infra, gympt-app

### 9-1. terraform/modules/iam/main.tf

```hcl
# before
"arn:aws:bedrock:*:337112169365:inference-profile/*"

# after
"arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*"
```

### 9-2. terraform/modules/rds/main.tf, elasticache/main.tf

```hcl
# before
egress {
  cidr_blocks = ["0.0.0.0/0"]
}

# after — 각 모듈에 data source 추가
data "aws_vpc" "this" { id = var.vpc_id }

egress {
  description = "All traffic within VPC"
  cidr_blocks = [data.aws_vpc.this.cidr_block]
}
```

### 9-3. terraform/environments/prod/main.tf

```hcl
# before
public_access_cidrs   = ["0.0.0.0/0"]
bucket = "gympt-fe-deploy-337112169365"
id = "E14Z61F5I2E9ZM"

# after
public_access_cidrs   = var.eks_public_access_cidrs
bucket = local.frontend_bucket  # "gympt-fe-deploy-${local.account_id}"
id = var.cloudfront_distribution_id
```

신규 변수는 `terraform.tfvars`(gitignore 됨)에서 관리:
```hcl
eks_public_access_cidrs    = ["0.0.0.0/0"]
cloudfront_distribution_id = "E14Z61F5I2E9ZM"
```

### 9-4. terraform/environments/dev/main.tf

```hcl
# before
public_access_cidrs = ["0.0.0.0/0"]

# after
public_access_cidrs = var.eks_public_access_cidrs
```

### 9-5. scripts/deploy-backend.sh

| 항목 | Before | After |
|------|--------|-------|
| ECR 저장소명 | `gympt-backend-api` | `gympt-${ENV}/backend-api` (실제 ECR 경로 일치) |
| GitOps values 경로 | `apps/gympt-${ENV}/backend-api/values.yaml` | `charts/backend-api/values-${ENV}.yaml` |
| ArgoCD 앱 이름 | `backend-api` | `backend-api-${ENV}` |

### 9-6. scripts/deploy-frontend.sh

```bash
# before — 하드코딩
S3_BUCKET="${2:-gympt-fe-deploy-337112169365}"
CLOUDFRONT_DISTRIBUTION_ID="${3:-E14Z61F5I2E9ZM}"

# after — 동적 조회
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="${2:-gympt-fe-deploy-${AWS_ACCOUNT_ID}}"
CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?contains(Aliases.Items, 'g2mpt.com')].Id | [0]" \
  --output text)
```

---

## 10. posture-analysis-service Pending — GPU 노드 그룹 0대

**일자:** 2026-06-01

### 증상
```
posture-analysis-service-prod-xxx   0/1   Pending   0   102m
kubectl describe pod → 0/3 nodes: node(s) didn't match Pod's node affinity/selector.
```

### 원인
`posture-analysis-service`는 MediaPipe GPU 추론을 위해 아래 설정으로 GPU 노드를 강제 요구:

```yaml
nodeSelector:
  gpu: "true"
tolerations:
  - key: nvidia.com/gpu
    operator: Equal
    value: "true"
    effect: NoSchedule
resources:
  limits:
    nvidia.com/gpu: 1
```

그런데 `gympt-prod-gpu` 관리형 노드 그룹의 `desiredSize: 0`으로 GPU 노드가 한 대도 없는 상태. Karpenter NodePool에도 GPU 인스턴스 타입이 포함되어 있지 않아 자동 프로비저닝도 불가.

```bash
aws eks describe-nodegroup \
  --cluster-name gympt-prod-eks --nodegroup-name gympt-prod-gpu \
  --query 'nodegroup.scalingConfig' --output json
# → {"desiredSize": 0, "minSize": 0, "maxSize": 3}
```

### 조치

```bash
# GPU 노드 그룹 1대로 스케일업
aws eks update-nodegroup-config \
  --cluster-name gympt-prod-eks \
  --nodegroup-name gympt-prod-gpu \
  --scaling-config desiredSize=1,minSize=1,maxSize=3 \
  --region ap-northeast-2

# 노드 Ready 대기 (약 3~5분 소요)
kubectl get nodes -w | grep gpu
```

### 확인

```bash
# GPU 노드가 Ready 되면 Pod 자동 스케줄링됨
kubectl get pods -n gympt-prod -l app.kubernetes.io/name=posture-analysis-service
```

### 학습 포인트
- GPU 노드 그룹은 비용 때문에 평소에 0대로 운영하지만, 서비스 배포 전에는 반드시 스케일업.
- Karpenter NodePool에 GPU 인스턴스 타입(예: `g4dn.xlarge`)을 추가하면 자동 프로비저닝 가능. 단, GPU 노드는 콜드스타트가 느리므로(NVIDIA 드라이버 설치 시간) 관리형 노드 그룹 최소 1대 유지가 권장됨.

---

## 11. Ingress 중복 — ALB 미프로비저닝으로 API 외부 접근 불가

**일자:** 2026-06-01

### 증상
```bash
kubectl get ingress -n gympt-prod
# NAME               CLASS   HOSTS           ADDRESS   PORTS
# backend-api        alb     api.g2mpt.com             80, 443
# backend-api-prod   alb     api.g2mpt.com             80, 443
# → ADDRESS 컬럼이 둘 다 비어있음 (ALB 미생성)
```
외부에서 `https://api.g2mpt.com` 접근 불가.

### 원인
동일한 호스트 `api.g2mpt.com`을 가리키는 ALB Ingress가 두 개 존재:

| Ingress 이름 | 대상 Service | 생성 경위 |
|-------------|-------------|---------|
| `backend-api` | `backend-api:8080` | 수동 생성(테스트용 추정) |
| `backend-api-prod` | `backend-api-prod:8080` | ArgoCD(Helm) 자동 생성 |

AWS ALB Ingress Controller는 동일 호스트를 가진 Ingress가 두 개 있으면 서로 충돌하여 ALB 프로비저닝이 실패하거나 지연됨.

### 조치

```bash
# 수동 생성된 이전 Ingress 삭제
kubectl delete ingress backend-api -n gympt-prod

# ALB 프로비저닝 확인 (2~3분 소요)
kubectl get ingress backend-api-prod -n gympt-prod -w
# → ADDRESS에 ALB DNS 주소가 표시되면 완료
```

ALB 주소 확인 후 Route53에서 `api.g2mpt.com` CNAME/ALIAS 레코드가 올바른 ALB를 가리키는지 확인:
```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id <ZONE_ID> \
  --query "ResourceRecordSets[?Name=='api.g2mpt.com.']"
```

### 학습 포인트
- ArgoCD로 관리되는 Ingress 외에 수동으로 `kubectl apply`한 Ingress가 남아있으면 이런 충돌이 발생.
- ALB Ingress Controller는 같은 호스트를 여러 Ingress로 나누는 `IngressGroup` 기능을 지원하지만, 이 프로젝트처럼 단순한 경우에는 Ingress 하나만 유지하는 것이 원칙.

---

## 12. agent-service·remediation-worker ExternalSecret 누락

**일자:** 2026-06-01

### 증상
```bash
kubectl get externalsecret -n gympt-prod
# agent-service-secrets      SecretSyncedError   False
# remediation-worker-secrets SecretSyncedError   False
```

### 원인
ExternalSecret이 참조하는 AWS Secrets Manager 경로가 존재하지 않음:

| ExternalSecret | 참조 경로 | 존재 여부 |
|---------------|----------|---------|
| `agent-service-secrets` | `gympt/prod/agent-service` | ❌ 없음 |
| `remediation-worker-secrets` | `gympt/prod/remediation-worker` | ❌ 없음 |

현재 Secrets Manager에는 `database`, `redis`, `jwt`, `bedrock`, `s3`, `sqs` 6개만 있음.

### 서비스 영향도
두 서비스 모두 ExternalSecret이 `Optional: true`로 설정되어 있어 **현재는 Pod가 Running 상태**. 단, 아래 기능은 정상 동작하지 않을 수 있음:

| 누락 값 | 영향 |
|---------|------|
| `BACKEND_API_KEY` | agent-service → backend-api 호출 시 인증 실패 가능 |
| `REDIS_PASSWORD` | Redis 세션/캐시 미사용 (기능 저하) |
| AWS 자격증명 | IRSA로 대체되므로 Bedrock 호출은 정상 |

### 조치 (배포 후 기능 이상 확인 시)

```bash
# agent-service용 시크릿 생성
aws secretsmanager create-secret \
  --name gympt/prod/agent-service \
  --region ap-northeast-2 \
  --secret-string '{
    "backend_api_key": "<발급된 API 키>",
    "redis_host": "master.gympt-prod-redis.8yu9pt.apn2.cache.amazonaws.com",
    "redis_port": "6379",
    "redis_password": "<gympt/prod/redis의 auth_token 값>",
    "dynamodb_interactions_table": "gympt-prod-agent-interactions"
  }'

# remediation-worker용 시크릿 생성
aws secretsmanager create-secret \
  --name gympt/prod/remediation-worker \
  --region ap-northeast-2 \
  --secret-string '{
    "backend_api_url": "http://backend-api-prod.gympt-prod.svc.cluster.local:8080",
    "backend_api_key": "<발급된 API 키>"
  }'

# ExternalSecret 강제 재동기화
kubectl annotate externalsecret agent-service-secrets \
  -n gympt-prod force-sync=$(date +%s) --overwrite
kubectl annotate externalsecret remediation-worker-secrets \
  -n gympt-prod force-sync=$(date +%s) --overwrite
```

### 학습 포인트
- ExternalSecret `Optional: true`는 시크릿 누락 시 Pod를 죽이지 않지만, 해당 환경변수가 없는 상태로 서비스가 동작하므로 기능 오류가 런타임에 발생.
- 초기 배포 전에 모든 ExternalSecret이 `SecretSynced: True` 상태인지 반드시 확인.

---

## 13. 현재 상태 및 남은 작업

### 현재 상태 (2026-06-01 기준)

| 서비스 | 상태 | 비고 |
|--------|------|------|
| agent-service-prod | ✅ Running (3/3) | Bedrock 호출 정상, Redis/API키 없이 동작 중 |
| kvs-consumer-service-prod | ✅ Running (2/2) | 정상 |
| remediation-worker-prod | ✅ Running (3/3) | API키 없이 동작 중 |
| report-service-prod | ✅ Running (2/2) | 정상 |
| backend-api-prod | ❌ CrashLoopBackOff | V4 마이그레이션 이미지 배포 필요 |
| posture-analysis-service-prod | ❌ Pending | GPU 노드 그룹 0대 |

### 재배포 전 반드시 해야 할 것 (순서대로)

```bash
# 1. 중복 Ingress 삭제 (ALB 프로비저닝 언블로킹)
kubectl delete ingress backend-api -n gympt-prod

# 2. GPU 노드 스케일업
aws eks update-nodegroup-config \
  --cluster-name gympt-prod-eks \
  --nodegroup-name gympt-prod-gpu \
  --scaling-config desiredSize=1,minSize=1,maxSize=3 \
  --region ap-northeast-2

# 3. gympt-app main 브랜치 push → CI/CD가 V4 마이그레이션 포함된 이미지 빌드/배포
```

### 배포 후 기능 검증 시 확인할 것

```bash
# 전체 Pod 상태
kubectl get pods -n gympt-prod

# Ingress ALB 주소 확인
kubectl get ingress backend-api-prod -n gympt-prod

# backend-api 헬스체크
curl https://api.g2mpt.com/actuator/health

# agent-service → backend-api 연동 확인 (API 키 이슈 시 12번 조치)
kubectl logs -f deployment/agent-service-prod -n gympt-prod | grep -E "ERROR|401|403"

# 전체 검증 스크립트
./scripts/verify-deployment.sh prod
```

### 중장기 개선 과제 (인프라 관점)

- [ ] `gympt-infra` 하드코딩 수정사항 커밋 → `terraform apply` (EKS 크로스 SG 룰 영속화)
- [ ] `gympt/prod/agent-service`, `gympt/prod/remediation-worker` Secrets Manager 생성
- [ ] EKS API 엔드포인트 `public_access_cidrs` 운영자 IP로 제한 (`terraform.tfvars` 수정 후 apply)
- [ ] `platform/network-policies/posture-analysis-netpol.yaml` 존재하지 않는 `ml-models` 네임스페이스 참조 수정
- [ ] Karpenter NodePool에 GPU 인스턴스 추가 (자동 스케일링 대응)

---

## 진단 명령어 모음

```bash
# Pod 전체 상태
kubectl get pods -n gympt-prod

# ExternalSecret 동기화 상태
kubectl get externalsecret -n gympt-prod

# 특정 Pod 로그
kubectl logs -f deployment/backend-api-prod -n gympt-prod --tail=50

# Karpenter 이슈
kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter | grep -E "ERROR|error" | tail -20
kubectl get nodeclaim

# DNS 테스트 (Karpenter 노드에서)
kubectl run dns-test --image=nicolaka/netshoot --restart=Never -n gympt-prod \
  --overrides='{"spec":{"nodeName":"<node-name>"}}' \
  --command -- nslookup <rds-endpoint>
kubectl delete pod dns-test -n gympt-prod

# SG 태그 확인
aws ec2 describe-subnets \
  --filters "Name=tag:karpenter.sh/discovery,Values=gympt-prod-eks" \
  --query 'Subnets[*].{ID:SubnetId,VPC:VpcId}' --output table --region ap-northeast-2

# Secrets Manager 값 확인
aws secretsmanager get-secret-value --secret-id gympt/prod/database \
  --region ap-northeast-2 --query SecretString --output text | python3 -m json.tool
```
