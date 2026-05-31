#!/bin/bash
# Deploy Backend API to EKS via ECR + GitOps

set -e

# Configuration
ENV=${1:-prod}
AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
SERVICE_NAME="gympt-backend-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GITOPS_REPO="$(cd "${SCRIPT_DIR}/../.." && pwd)/gympt-gitops"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Backend API Deployment - ${ENV}${NC}"
echo -e "${GREEN}========================================${NC}"

# Validate environment
if [[ "$ENV" != "prod" && "$ENV" != "dev" ]]; then
    echo -e "${RED}Error: Environment must be 'prod' or 'dev'${NC}"
    exit 1
fi

# Step 1: Build and test
echo -e "${YELLOW}Step 1: Building and testing...${NC}"
cd backend-api
./gradlew clean build test
if [ $? -ne 0 ]; then
    echo -e "${RED}Build or tests failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Build and tests passed${NC}"

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
cd ..
IMAGE_TAG=$(git rev-parse --short HEAD)
docker build -t ${SERVICE_NAME}:${IMAGE_TAG} -f backend-api/Dockerfile .
docker tag ${SERVICE_NAME}:${IMAGE_TAG} ${SERVICE_NAME}:latest
echo -e "${GREEN}✓ Docker image built: ${SERVICE_NAME}:${IMAGE_TAG}${NC}"

# Step 3: Login to ECR
echo -e "${YELLOW}Step 3: Authenticating with ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REGISTRY}
echo -e "${GREEN}✓ ECR authentication successful${NC}"

# Step 4: Tag and push to ECR
echo -e "${YELLOW}Step 4: Pushing image to ECR...${NC}"
docker tag ${SERVICE_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG}
docker tag ${SERVICE_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${SERVICE_NAME}:latest
docker tag ${SERVICE_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${SERVICE_NAME}:${ENV}-latest

docker push ${ECR_REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG}
docker push ${ECR_REGISTRY}/${SERVICE_NAME}:latest
docker push ${ECR_REGISTRY}/${SERVICE_NAME}:${ENV}-latest

echo -e "${GREEN}✓ Image pushed to ECR${NC}"
echo -e "  - ${ECR_REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG}"
echo -e "  - ${ECR_REGISTRY}/${SERVICE_NAME}:latest"
echo -e "  - ${ECR_REGISTRY}/${SERVICE_NAME}:${ENV}-latest"

# Step 5: Update GitOps repository
echo -e "${YELLOW}Step 5: Updating GitOps repository...${NC}"
if [ ! -d "${GITOPS_REPO}" ]; then
    echo -e "${RED}Error: GitOps repository not found at ${GITOPS_REPO}${NC}"
    exit 1
fi

cd ${GITOPS_REPO}
git pull origin main

# Update image tag in values.yaml
VALUES_FILE="apps/gympt-${ENV}/backend-api/values.yaml"
if [ ! -f "${VALUES_FILE}" ]; then
    echo -e "${RED}Error: Values file not found: ${VALUES_FILE}${NC}"
    exit 1
fi

# Update tag using sed
sed -i.bak "s|tag: .*|tag: \"${IMAGE_TAG}\"|" ${VALUES_FILE}
rm -f ${VALUES_FILE}.bak

echo -e "${GREEN}✓ Updated ${VALUES_FILE} with tag: ${IMAGE_TAG}${NC}"

# Commit and push
git add ${VALUES_FILE}
git commit -m "Deploy backend-api ${IMAGE_TAG} to ${ENV}

Commit: ${IMAGE_TAG}
Environment: ${ENV}
Service: backend-api
" || echo "No changes to commit"

git push origin main
echo -e "${GREEN}✓ GitOps repository updated${NC}"

# Step 6: Wait for Argo CD sync (optional)
echo -e "${YELLOW}Step 6: Waiting for Argo CD sync...${NC}"
echo -e "${YELLOW}Checking Argo CD application status...${NC}"

# Check if argocd CLI is installed
if command -v argocd &> /dev/null; then
    argocd app sync backend-api --force || true
    argocd app wait backend-api --health --timeout 300 || echo "Argo CD sync timed out"
else
    echo -e "${YELLOW}Argo CD CLI not installed. Skipping auto-sync.${NC}"
    echo -e "${YELLOW}Monitor deployment at: https://argocd.g2mpt.com${NC}"
fi

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${ENV}"
echo -e "Service: backend-api"
echo -e "Image Tag: ${IMAGE_TAG}"
echo -e "ECR Image: ${ECR_REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG}"
echo -e "GitOps Updated: Yes"
echo -e ""
echo -e "${GREEN}Deployment initiated successfully!${NC}"
echo -e "Monitor at: https://argocd.g2mpt.com/applications/backend-api"
echo -e ""
echo -e "Verify deployment:"
echo -e "  kubectl get pods -n gympt-${ENV} -l app=backend-api"
echo -e "  kubectl logs -f deployment/backend-api -n gympt-${ENV}"
echo -e ""
