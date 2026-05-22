#!/bin/bash

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ENV=${1:-prod}

echo "🐳 Building all services for environment: ${ENV}"
echo "📁 Working directory: ${PROJECT_ROOT}"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-ap-northeast-2}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "📍 ECR Registry: ${ECR_REGISTRY}"

aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Change to project root
cd "${PROJECT_ROOT}"

SERVICES=(
  "backend-api"
  "agent-service"
  "posture-analysis-service"
  "remediation-worker"
)

for SERVICE in "${SERVICES[@]}"; do
  echo ""
  echo "🔨 Building ${SERVICE}..."

  cd "${SERVICE}"

  IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
  IMAGE_NAME="gympt-${ENV}/${SERVICE}"
  FULL_IMAGE="${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
  LATEST_IMAGE="${ECR_REGISTRY}/${IMAGE_NAME}:latest"

  echo "  Building: ${FULL_IMAGE}"
  docker build --platform linux/amd64 -t ${FULL_IMAGE} -t ${LATEST_IMAGE} .

  echo "  Pushing: ${FULL_IMAGE}"
  docker push ${FULL_IMAGE} || echo "Warning: Push ${FULL_IMAGE} had warnings"
  docker push ${LATEST_IMAGE} || echo "Warning: Push ${LATEST_IMAGE} had warnings"

  echo "  ✓ ${SERVICE} built and pushed successfully"

  cd ..
done

echo ""
echo "✅ All services built and pushed to ECR"
echo ""
echo "📝 Image tags:"
for SERVICE in "${SERVICES[@]}"; do
  IMAGE_TAG=$(git rev-parse --short HEAD)
  echo "  ${SERVICE}: ${IMAGE_TAG}"
done
echo ""
echo "Next step: Update image tags in gympt-gitops repo"
