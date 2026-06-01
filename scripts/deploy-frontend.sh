#!/bin/bash

# GYMPT Frontend Deployment Script
# Uploads built frontend to S3 and invalidates CloudFront cache

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Arguments
ENV="${1:-prod}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="${2:-gympt-fe-deploy-${AWS_ACCOUNT_ID}}"
CLOUDFRONT_DISTRIBUTION_ID="${3:-}"

# CloudFront ID를 인자로 주지 않은 경우 태그로 자동 조회
if [ -z "${CLOUDFRONT_DISTRIBUTION_ID}" ]; then
    CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?contains(Aliases.Items, 'g2mpt.com')].Id | [0]" \
        --output text 2>/dev/null || echo "")
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BUILD_DIR="${FRONTEND_DIR}/out"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}GYMPT Frontend Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "S3 Bucket: ${S3_BUCKET}"
echo -e "CloudFront: ${CLOUDFRONT_DISTRIBUTION_ID:-None}"
echo -e "Environment: ${ENV}"
echo ""

# Check if build exists
if [ ! -d "${BUILD_DIR}" ]; then
    echo -e "${RED}Error: Build directory not found${NC}"
    echo -e "${YELLOW}Run ./scripts/build-frontend.sh first${NC}"
    exit 1
fi

# Verify AWS credentials
echo -e "${BLUE}Verifying AWS credentials...${NC}"
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials valid${NC}"

# Upload to S3
echo -e "${BLUE}Uploading files to S3...${NC}"
cd "${BUILD_DIR}"

# Upload HTML files (no cache)
echo -e "${YELLOW}Uploading HTML files...${NC}"
aws s3 sync . "s3://${S3_BUCKET}/" \
    --exclude "*" \
    --include "*.html" \
    --cache-control "public, max-age=0, must-revalidate" \
    --delete

# Upload static assets (long cache)
echo -e "${YELLOW}Uploading static assets...${NC}"
aws s3 sync . "s3://${S3_BUCKET}/" \
    --exclude "*.html" \
    --cache-control "public, max-age=31536000, immutable" \
    --delete

echo -e "${GREEN}✓ Upload complete${NC}"

# Invalidate CloudFront cache
if [ -n "${CLOUDFRONT_DISTRIBUTION_ID}" ]; then
    echo -e "${BLUE}Invalidating CloudFront cache...${NC}"
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)

    echo -e "${GREEN}✓ Invalidation created: ${INVALIDATION_ID}${NC}"
    echo -e "${YELLOW}Waiting for invalidation to complete...${NC}"

    aws cloudfront wait invalidation-completed \
        --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --id "${INVALIDATION_ID}"

    echo -e "${GREEN}✓ CloudFront cache invalidated${NC}"
fi

# Get CloudFront URL if distribution ID provided
if [ -n "${CLOUDFRONT_DISTRIBUTION_ID}" ]; then
    CF_DOMAIN=$(aws cloudfront get-distribution \
        --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --query 'Distribution.DomainName' \
        --output text)

    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "CloudFront URL: https://${CF_DOMAIN}"
    echo ""
else
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Upload Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "S3 Bucket: s3://${S3_BUCKET}"
    echo ""
fi
