#!/bin/bash

# GYMPT Application Repository Checker
# Validates project structure and identifies missing components

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0
WARNINGS=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}GYMPT Application Repository Structure Check${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to check if file/directory exists
check_exists() {
    local path="$1"
    local type="$2"  # "file" or "dir"
    local description="$3"
    local priority="$4"  # "critical", "important", "optional"

    TOTAL=$((TOTAL + 1))

    if [ "$type" = "file" ]; then
        if [ -f "${PROJECT_ROOT}/${path}" ]; then
            echo -e "${GREEN}✓${NC} ${description}"
            PASSED=$((PASSED + 1))
            return 0
        fi
    else
        if [ -d "${PROJECT_ROOT}/${path}" ]; then
            echo -e "${GREEN}✓${NC} ${description}"
            PASSED=$((PASSED + 1))
            return 0
        fi
    fi

    if [ "$priority" = "critical" ]; then
        echo -e "${RED}✗${NC} ${description} (CRITICAL)"
        FAILED=$((FAILED + 1))
    elif [ "$priority" = "important" ]; then
        echo -e "${YELLOW}⚠${NC} ${description} (Missing)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${YELLOW}○${NC} ${description} (Optional)"
        WARNINGS=$((WARNINGS + 1))
    fi
    return 1
}

# Repository Structure
echo -e "\n${BLUE}=== Repository Structure ===${NC}"
check_exists ".env.example" "file" "Root .env.example" "critical"
check_exists ".gitignore" "file" "Root .gitignore" "critical"
check_exists "README.md" "file" "Root README.md" "critical"
check_exists "CHECKLIST.md" "file" "Project checklist" "important"
check_exists "docs" "dir" "Documentation directory" "important"

# Local Development
echo -e "\n${BLUE}=== Local Development ===${NC}"
check_exists "local/docker-compose.yml" "file" "Main docker-compose" "critical"
check_exists "local/docker-compose.observability.yml" "file" "Observability stack" "important"
check_exists "local/docker-compose.test.yml" "file" "Test environment" "optional"
check_exists "local/README.md" "file" "Local development guide" "important"
check_exists "local/init-scripts" "dir" "Database init scripts" "optional"

# Security & Secrets
echo -e "\n${BLUE}=== Security & Secrets ===${NC}"
check_exists "docs/env-and-secrets.md" "file" "Secret management docs" "critical"
check_exists "docs/secret-rotation.md" "file" "Secret rotation procedures" "optional"
check_exists "docs/security-checklist.md" "file" "Security best practices" "optional"

# Backend API
echo -e "\n${BLUE}=== Backend API (Spring Boot) ===${NC}"
check_exists "backend-api/README.md" "file" "Backend API README" "critical"
check_exists "backend-api/Dockerfile" "file" "Backend API Dockerfile" "critical"
check_exists "backend-api/.env.example" "file" "Backend API .env.example" "critical"
check_exists "backend-api/src" "dir" "Backend API source code" "critical"
check_exists "backend-api/build.gradle" "file" "Backend API Gradle config" "critical"
check_exists "backend-api/src/test" "dir" "Backend API tests" "important"

# Agent Service
echo -e "\n${BLUE}=== Agent Service (Python/FastAPI) ===${NC}"
check_exists "agent-service/README.md" "file" "Agent Service README" "critical"
check_exists "agent-service/Dockerfile" "file" "Agent Service Dockerfile" "critical"
check_exists "agent-service/.env.example" "file" "Agent Service .env.example" "critical"
check_exists "agent-service/app" "dir" "Agent Service source code" "critical"
check_exists "agent-service/requirements.txt" "file" "Agent Service requirements" "critical"
check_exists "agent-service/tests" "dir" "Agent Service tests" "important"

# Posture Analysis Service
echo -e "\n${BLUE}=== Posture Analysis Service (Python/FastAPI + GPU) ===${NC}"
check_exists "posture-analysis-service/README.md" "file" "Posture Analysis README" "critical"
check_exists "posture-analysis-service/Dockerfile" "file" "Posture Analysis Dockerfile" "critical"
check_exists "posture-analysis-service/.env.example" "file" "Posture Analysis .env.example" "critical"
check_exists "posture-analysis-service/app" "dir" "Posture Analysis source code" "critical"
check_exists "posture-analysis-service/requirements.txt" "file" "Posture Analysis requirements" "critical"
check_exists "posture-analysis-service/models" "dir" "ML model files" "important"
check_exists "posture-analysis-service/tests" "dir" "Posture Analysis tests" "important"

# Report Service
echo -e "\n${BLUE}=== Report Service (Spring Boot) ===${NC}"
check_exists "report-service/README.md" "file" "Report Service README" "important"
check_exists "report-service/Dockerfile" "file" "Report Service Dockerfile" "important"
check_exists "report-service/.env.example" "file" "Report Service .env.example" "important"
check_exists "report-service/src" "dir" "Report Service source code" "important"

# Notification Service
echo -e "\n${BLUE}=== Notification Service (Spring Boot) ===${NC}"
check_exists "notification-service/README.md" "file" "Notification Service README" "important"
check_exists "notification-service/Dockerfile" "file" "Notification Service Dockerfile" "important"
check_exists "notification-service/src" "dir" "Notification Service source code" "important"

# Remediation Worker
echo -e "\n${BLUE}=== Remediation Worker (Python/FastAPI) ===${NC}"
check_exists "remediation-worker/README.md" "file" "Remediation Worker README" "critical"
check_exists "remediation-worker/Dockerfile" "file" "Remediation Worker Dockerfile" "critical"
check_exists "remediation-worker/app" "dir" "Remediation Worker source code" "critical"
check_exists "remediation-worker/requirements.txt" "file" "Remediation Worker requirements" "critical"
check_exists "remediation-worker/tests" "dir" "Remediation Worker tests" "important"

# Frontend
echo -e "\n${BLUE}=== Frontend (Next.js) ===${NC}"
check_exists "frontend/README.md" "file" "Frontend README" "critical"
check_exists "frontend/package.json" "file" "Frontend package.json" "critical"
check_exists "frontend/.env.example" "file" "Frontend .env.example" "critical"
check_exists "frontend/src" "dir" "Frontend source code" "critical"
check_exists "frontend/src/lib/api-client.ts" "file" "API client" "critical"
check_exists "frontend/src/lib/websocket-client.ts" "file" "WebSocket client" "critical"
check_exists "frontend/src/lib/kvs-client.ts" "file" "KVS WebRTC client" "critical"
check_exists "frontend/src/__tests__" "dir" "Frontend Jest tests" "important"
check_exists "frontend/cypress" "dir" "Frontend E2E tests" "optional"

# Lambda Functions
echo -e "\n${BLUE}=== Lambda Functions ===${NC}"
check_exists "lambdas/README.md" "file" "Lambdas README" "important"
check_exists "lambdas/report-generator" "dir" "Report generator lambda" "important"
check_exists "lambdas/posture-event-processor" "dir" "Posture event processor" "important"
check_exists "lambdas/thumbnail-generator" "dir" "Thumbnail generator" "important"
check_exists "lambdas/wearable-sync" "dir" "Wearable sync lambda" "important"
check_exists "lambdas/recommendation-update" "dir" "Recommendation update lambda" "important"
check_exists "lambdas/notification" "dir" "Notification lambda" "important"
check_exists "lambdas/export" "dir" "Export lambda" "important"

# Shared Libraries
echo -e "\n${BLUE}=== Shared Libraries ===${NC}"
check_exists "shared" "dir" "Shared libraries directory" "optional"
check_exists "shared/error-handling" "dir" "Common error handling" "optional"
check_exists "shared/logging" "dir" "Structured logging utilities" "optional"

# CI/CD
echo -e "\n${BLUE}=== CI/CD Workflows ===${NC}"
check_exists ".github/workflows/backend-api-ci.yml" "file" "Backend API CI/CD" "critical"
check_exists ".github/workflows/agent-service-ci.yml" "file" "Agent Service CI/CD" "critical"
check_exists ".github/workflows/posture-analysis-service-ci.yml" "file" "Posture Analysis CI/CD" "critical"
check_exists ".github/workflows/frontend-deploy.yml" "file" "Frontend deployment" "critical"
check_exists ".github/workflows/lambda-package.yml" "file" "Lambda packaging" "important"
check_exists ".github/workflows/report-service-ci.yml" "file" "Report Service CI/CD" "optional"
check_exists ".github/workflows/remediation-worker-ci.yml" "file" "Remediation Worker CI/CD" "important"
check_exists ".github/workflows/integration-tests.yml" "file" "Integration tests" "optional"

# Testing Scripts
echo -e "\n${BLUE}=== Testing Scripts ===${NC}"
check_exists "scripts/test-local.sh" "file" "Local test runner" "important"
check_exists "scripts/test-integration.sh" "file" "Integration tests" "optional"
check_exists "scripts/test-e2e.sh" "file" "E2E tests" "optional"
check_exists "scripts/setup-test-db.sh" "file" "Test DB setup" "optional"

# Deployment Scripts
echo -e "\n${BLUE}=== Deployment Scripts ===${NC}"
check_exists "scripts/dev-up.sh" "file" "Start local dev" "important"
check_exists "scripts/dev-down.sh" "file" "Stop local dev" "important"
check_exists "scripts/deploy-dev.sh" "file" "Deploy to dev" "optional"
check_exists "scripts/deploy-prod.sh" "file" "Deploy to prod" "optional"
check_exists "scripts/rollback.sh" "file" "Rollback deployment" "optional"

# Summary
echo -e "\n${BLUE}==================================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "Total checks:     ${TOTAL}"
echo -e "${GREEN}Passed:           ${PASSED}${NC}"
echo -e "${YELLOW}Warnings:         ${WARNINGS}${NC}"
echo -e "${RED}Failed (Critical): ${FAILED}${NC}"

PERCENTAGE=$((PASSED * 100 / TOTAL))
echo -e "\nCompletion:       ${PERCENTAGE}%"

# Critical issues
if [ $FAILED -gt 0 ]; then
    echo -e "\n${RED}⚠ CRITICAL ISSUES FOUND${NC}"
    echo -e "Please address the failed items above before proceeding."
    exit 1
fi

# Recommendations
echo -e "\n${BLUE}=== Top Recommendations ===${NC}"
echo -e "1. ${YELLOW}Implement service source code${NC} (Backend API, Agent Service, Posture Analysis)"
echo -e "2. ${YELLOW}Add comprehensive test coverage${NC} (Unit, integration, E2E tests)"
echo -e "3. ${YELLOW}Implement Lambda functions${NC} (7 functions need implementation)"
echo -e "4. ${YELLOW}Create deployment automation${NC} (dev-up.sh, deploy-dev.sh, etc.)"
echo -e "5. ${YELLOW}Add shared libraries${NC} (Error handling, logging, validation)"

echo -e "\n${GREEN}✓ Project structure validation complete${NC}\n"
exit 0
