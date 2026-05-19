#!/bin/bash

set -e

ENV=${1:-prod}

echo "🐳 Building all services for environment: ${ENV}"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-ap-northeast-2}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "📍 ECR Registry: ${ECR_REGISTRY}"

aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

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

  IMAGE_TAG=$(git rev-parse --short HEAD)
  IMAGE_NAME="gympt-${ENV}/${SERVICE}"
  FULL_IMAGE="${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
  LATEST_IMAGE="${ECR_REGISTRY}/${IMAGE_NAME}:latest"

  echo "  Building: ${FULL_IMAGE}"
  docker build -t ${FULL_IMAGE} -t ${LATEST_IMAGE} .

  echo "  Pushing: ${FULL_IMAGE}"
  docker push ${FULL_IMAGE}
  docker push ${LATEST_IMAGE}

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
