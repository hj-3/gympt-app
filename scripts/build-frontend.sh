#!/bin/bash

# GYMPT Frontend Build Script
# Builds Next.js frontend for production

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}GYMPT Frontend Build${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if frontend directory exists
if [ ! -d "${FRONTEND_DIR}" ]; then
    echo -e "${RED}Error: Frontend directory not found${NC}"
    exit 1
fi

cd "${FRONTEND_DIR}"

# Check environment variables
echo -e "${YELLOW}Checking environment variables...${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}Warning: .env.production not found, using .env.example${NC}"
    cp .env.example .env.production
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
npm ci

# Run linting
echo -e "${BLUE}Running linter...${NC}"
npm run lint || echo -e "${YELLOW}Warning: Linting issues found${NC}"

# Run type check
echo -e "${BLUE}Type checking...${NC}"
npm run build

# Build output
echo -e "${GREEN}✓ Frontend build complete!${NC}"
echo -e "${GREEN}Build output: ${FRONTEND_DIR}/out${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Upload to S3: ./scripts/deploy-frontend.sh <s3-bucket-name>"
echo -e "  2. Invalidate CloudFront cache"
echo ""
