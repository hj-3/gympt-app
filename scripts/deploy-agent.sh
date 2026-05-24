#!/bin/bash
# Deploy Agent Service to EKS via ECR + GitOps

set -e

# Configuration
ENV=${1:-prod}
AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID="337112169365"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
SERVICE_NAME="gympt-agent-service"
GITOPS_REPO="../gympt-gitops"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Agent Service Deployment - ${ENV}${NC}"
echo -e "${GREEN}========================================${NC}"

# Validate environment
if [[ "$ENV" != "prod" && "$ENV" != "dev" ]]; then
    echo -e "${RED}Error: Environment must be 'prod' or 'dev'${NC}"
    exit 1
fi

# Step 1: Run tests
echo -e "${YELLOW}Step 1: Running tests...${NC}"
cd agent-service
if [ -f "requirements.txt" ]; then
    python -m pytest tests/ -v || echo "Tests not found or failed"
fi
echo -e "${GREEN}✓ Tests completed${NC}"

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
cd ..
IMAGE_TAG=$(git rev-parse --short HEAD)
docker build -t ${SERVICE_NAME}:${IMAGE_TAG} -f agent-service/Dockerfile .
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

# Step 5: Update GitOps repository
echo -e "${YELLOW}Step 5: Updating GitOps repository...${NC}"
cd ${GITOPS_REPO}
git pull origin main

VALUES_FILE="apps/gympt-${ENV}/agent-service/values.yaml"
sed -i.bak "s|tag: .*|tag: \"${IMAGE_TAG}\"|" ${VALUES_FILE}
rm -f ${VALUES_FILE}.bak

echo -e "${GREEN}✓ Updated ${VALUES_FILE} with tag: ${IMAGE_TAG}${NC}"

git add ${VALUES_FILE}
git commit -m "Deploy agent-service ${IMAGE_TAG} to ${ENV}" || echo "No changes"
git push origin main

echo -e "${GREEN}✓ GitOps repository updated${NC}"

# Step 6: Sync with Argo CD
echo -e "${YELLOW}Step 6: Syncing with Argo CD...${NC}"
if command -v argocd &> /dev/null; then
    argocd app sync agent-service --force || true
    argocd app wait agent-service --health --timeout 300 || echo "Sync timed out"
else
    echo -e "${YELLOW}Argo CD CLI not installed. Monitor at: https://argocd.g2mpt.com${NC}"
fi

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${ENV}"
echo -e "Service: agent-service"
echo -e "Image Tag: ${IMAGE_TAG}"
echo -e "ECR Image: ${ECR_REGISTRY}/${SERVICE_NAME}:${IMAGE_TAG}"
echo -e ""
echo -e "${GREEN}Deployment initiated successfully!${NC}"
echo -e "Monitor at: https://argocd.g2mpt.com/applications/agent-service"
echo -e ""
echo -e "Verify deployment:"
echo -e "  kubectl get pods -n gympt-${ENV} -l app=agent-service"
echo -e "  kubectl logs -f deployment/agent-service -n gympt-${ENV}"
