# GYMPT Application - AI Personal Training Platform

> **GYMPT**: Your AI-powered personal trainer that combines real-time posture analysis, personalized workout planning, and intelligent fitness coaching.

[![Production](https://img.shields.io/badge/production-g2mpt.com-success)](https://g2mpt.com)
[![Dev Environment](https://img.shields.io/badge/dev-dev.g2mpt.com-blue)](https://dev.g2mpt.com)
[![AWS](https://img.shields.io/badge/AWS-EKS-orange)](https://aws.amazon.com/eks/)
[![Bedrock Agent](https://img.shields.io/badge/AWS-Bedrock_Agent-blueviolet)](https://aws.amazon.com/bedrock/)

## 🎯 Overview

GYMPT is a cloud-native, microservices-based AI personal training platform that provides:

- **🤖 AI Personal Trainer**: Bedrock Agent with RAG-based knowledge for personalized coaching
- **📹 Real-time Posture Analysis**: Computer vision-based exercise form correction
- **💪 Personalized Workout Plans**: AI-generated routines based on body profile and goals
- **📊 Intelligent Reports**: Comprehensive workout analytics with AI insights
- **💬 Interactive Chat**: Conversational PT with memory and context awareness
- **📱 Mobile-First UI**: Responsive design for seamless mobile experience

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                         │
│                  https://g2mpt.com (S3 + CloudFront)             │
│                    AWS Cognito Authentication                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                Backend API (Spring Boot 3.2)                      │
│              https://api.g2mpt.com/api/v1                        │
│              OAuth2 Resource Server (Cognito JWT)                │
└───────┬────────────┬───────────────┬────────────────┬───────────┘
        │            │               │                │
        ↓            ↓               ↓                ↓
┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐
│  Agent   │  │  Posture    │  │  Report  │  │  WebSocket   │
│  Service │  │  Analysis   │  │  Service │  │   Server     │
│ (FastAPI)│  │  (Python)   │  │ (Python) │  │ (Spring WS)  │
└────┬─────┘  └──────┬──────┘  └────┬─────┘  └──────────────┘
     │               │              │
     ↓               ↓              ↓
┌─────────────┐  ┌────────┐  ┌──────────┐
│   Bedrock   │  │  KVS   │  │ DynamoDB │
│    Agent    │  │        │  │PostgreSQL│
│  + KB (RAG) │  │        │  │    S3    │
└─────────────┘  └────────┘  └──────────┘
```

## 📦 Microservices

### 1. Backend API (Spring Boot)
**Port**: 8080  
**Path**: `/backend-api`

- User management and authentication
- Body profile and workout goal CRUD
- Workout session orchestration
- Posture feedback aggregation
- OAuth2 JWT validation (Cognito)

**Key Features**:
- Spring Security with Cognito integration
- PostgreSQL (user data) + DynamoDB (time-series data)
- RESTful API with OpenAPI documentation
- IRSA for AWS service access

### 2. Agent Service (FastAPI)
**Port**: 8001  
**Path**: `/agent-service`

- Bedrock Agent integration
- Workout plan generation (RAG-based)
- Real-time posture feedback analysis
- Workout report generation
- Interactive PT chat with memory

**Key Features**:
- AWS Bedrock Agent Runtime client
- Knowledge Base for exercise/nutrition info
- Action Groups for user data access
- Session-based conversation memory

### 3. Posture Analysis Service (Python)
**Port**: 8002  
**Path**: `/posture-analysis`

- Real-time video frame analysis
- Pose estimation with MediaPipe/OpenPose
- Exercise-specific form validation
- Angle and position calculations
- KVS integration for video streaming

**Key Features**:
- ML model for posture detection
- WebSocket support for real-time feedback
- Frame-by-frame analysis
- Exercise library validation rules

### 4. Report Service (Python)
**Port**: 8003  
**Path**: `/report-service`

- Workout report generation
- PDF creation with charts
- S3 report storage
- Historical trend analysis

**Key Features**:
- ReportLab for PDF generation
- Matplotlib for data visualization
- DynamoDB query for historical data
- Pre-signed S3 URLs for report access

## 🚀 Getting Started

### Prerequisites

- Docker Desktop (for local development)
- AWS CLI configured with credentials
- kubectl and helm installed
- Node.js 18+ (for frontend)
- Python 3.11+ (for Python services)
- Java 17+ (for backend)

### Local Development

#### 1. Backend API

```bash
cd backend-api
./gradlew bootRun
```

Runs on `http://localhost:8080`

#### 2. Agent Service

```bash
cd agent-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

Runs on `http://localhost:8001`

#### 3. Posture Analysis Service

```bash
cd posture-analysis
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8002
```

Runs on `http://localhost:8002`

#### 4. Report Service

```bash
cd report-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8003
```

Runs on `http://localhost:8003`

#### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3000`

### Environment Variables

Each service requires specific environment variables. See `.env.example` files in each directory.

**Backend API** (`backend-api/.env`):
```env
SPRING_PROFILES_ACTIVE=local
COGNITO_USER_POOL_ID=ap-northeast-2_XXXXXXXXX
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
COGNITO_REGION=ap-northeast-2
DATABASE_URL=jdbc:postgresql://localhost:5432/gympt
DYNAMODB_TABLE_PREFIX=gympt-local
AWS_REGION=ap-northeast-2
```

**Agent Service** (`agent-service/.env`):
```env
BEDROCK_AGENT_ID=XXXXXXXXXX
BEDROCK_AGENT_ALIAS_ID=YYYYYYYYYY
BEDROCK_REGION=us-west-2
AWS_REGION=ap-northeast-2
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api/v1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=ap-northeast-2_XXXXXXXXX
NEXT_PUBLIC_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
NEXT_PUBLIC_COGNITO_REGION=ap-northeast-2
```

## 📚 Documentation

- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture and design decisions
- **[DEPLOYMENT.md](../DEPLOYMENT.md)** - Deployment guide for all environments
- **[MANUAL_SETUP.md](../MANUAL_SETUP.md)** - One-time AWS service setup (Cognito, SES, S3, etc.)
- **[BEDROCK_AGENT_SETUP.md](../BEDROCK_AGENT_SETUP.md)** - Bedrock Agent and Knowledge Base setup
- **[API.md](./API.md)** - API documentation for all services
- **[SES_SETUP.md](../SES_SETUP.md)** - Amazon SES configuration for email delivery

## 🔧 Building and Deployment

### Docker Build

Each service has a Dockerfile for containerization:

```bash
# Backend API
docker build -t gympt/backend-api:latest -f backend-api/Dockerfile .

# Agent Service
docker build -t gympt/agent-service:latest -f agent-service/Dockerfile .

# Posture Analysis Service
docker build -t gympt/posture-analysis:latest -f posture-analysis/Dockerfile .

# Report Service
docker build -t gympt/report-service:latest -f report-service/Dockerfile .
```

### Push to ECR

```bash
# Authenticate to ECR
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin 337112169365.dkr.ecr.ap-northeast-2.amazonaws.com

# Tag and push
docker tag gympt/backend-api:latest \
  337112169365.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-backend-api:latest
docker push 337112169365.dkr.ecr.ap-northeast-2.amazonaws.com/gympt-backend-api:latest
```

### Deploy to EKS

Deployment is managed via GitOps with Argo CD. See [gympt-gitops](../gympt-gitops/README.md) repository.

```bash
# Update Helm values in gympt-gitops
cd ../gympt-gitops/apps/gympt-prod/backend-api
# Edit values.yaml
git commit -m "Update backend-api image tag"
git push

# Argo CD will automatically sync
```

## 🧪 Testing

### Backend API Tests

```bash
cd backend-api
./gradlew test
```

### Agent Service Tests

```bash
cd agent-service
pytest tests/ -v
```

### Posture Analysis Tests

```bash
cd posture-analysis
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## 📊 Monitoring

### Health Checks

- Backend API: `https://api.g2mpt.com/api/v1/health`
- Agent Service: `https://api.g2mpt.com/agent/health`
- Posture Analysis: `https://api.g2mpt.com/posture/health`
- Report Service: `https://api.g2mpt.com/report/health`

### CloudWatch Logs

```bash
# Backend API logs
kubectl logs -f deployment/backend-api -n gympt-prod

# Agent Service logs
kubectl logs -f deployment/agent-service -n gympt-prod
```

### Metrics

Prometheus metrics are exposed at `/actuator/prometheus` (Backend API) and `/metrics` (FastAPI services).

## 🔐 Security

### Authentication Flow

1. User signs up via Cognito (username + email + password)
2. Email verification (via SES in production)
3. User logs in with username/password
4. Cognito returns JWT tokens (ID token, access token, refresh token)
5. Frontend stores tokens in `AuthContext`
6. Backend validates JWT using Cognito public keys
7. Backend maps `cognito:sub` to internal User UUID

### Authorization

- Spring Security with OAuth2 Resource Server
- Role-based access control (ROLE_USER, ROLE_ADMIN)
- IRSA for pod-level AWS service access

### Secrets Management

- AWS Secrets Manager for sensitive values
- Kubernetes Secrets for pod environment variables
- External Secrets Operator for GitOps integration

## 🚨 Troubleshooting

### Common Issues

**Issue**: "Access Denied" errors from AWS services
- **Solution**: Verify IRSA is properly configured. Check service account annotations and IAM role trust policy.

**Issue**: Cognito JWT validation fails
- **Solution**: Ensure `COGNITO_USER_POOL_ID` and `COGNITO_REGION` are correct. Check Cognito public keys are accessible.

**Issue**: Bedrock Agent invocation fails
- **Solution**: Verify `BEDROCK_AGENT_ID` and `BEDROCK_AGENT_ALIAS_ID`. Ensure agent is in "Prepared" state.

**Issue**: Frontend can't connect to backend
- **Solution**: Check CORS configuration in `SecurityConfig.java`. Verify `NEXT_PUBLIC_API_BASE_URL` is correct.

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Auth**: AWS Amplify (Cognito)
- **State**: Zustand
- **HTTP**: Axios

### Backend
- **Framework**: Spring Boot 3.2
- **Language**: Java 17
- **Auth**: OAuth2 Resource Server
- **Database**: PostgreSQL 15 + DynamoDB
- **ORM**: Spring Data JPA
- **API Docs**: SpringDoc OpenAPI

### Python Services
- **Framework**: FastAPI
- **Language**: Python 3.11
- **AI/ML**: AWS Bedrock, MediaPipe
- **HTTP**: Boto3, HTTPX
- **Testing**: Pytest

### Infrastructure
- **Container**: Docker + EKS
- **Orchestration**: Kubernetes + Helm
- **GitOps**: Argo CD
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

### AWS Services
- **Compute**: EKS (EC2)
- **Auth**: Cognito
- **AI**: Bedrock Agent + Knowledge Base
- **Storage**: S3, DynamoDB, RDS (PostgreSQL)
- **CDN**: CloudFront
- **Streaming**: Kinesis Video Streams
- **Monitoring**: CloudWatch
- **Email**: SES

## 📝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Write tests
4. Update documentation
5. Submit a pull request

## 📄 License

Proprietary - All rights reserved

## 👥 Team

Cloud Architecture Team - GYMPT Platform

## 🔗 Links

- **Production**: https://g2mpt.com
- **API**: https://api.g2mpt.com
- **Dev Environment**: https://dev.g2mpt.com
- **Infrastructure**: [gympt-infra](../gympt-infra/README.md)
- **GitOps**: [gympt-gitops](../gympt-gitops/README.md)

---

**Last Updated**: 2026-05-24
