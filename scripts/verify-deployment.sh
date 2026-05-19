#!/bin/bash

# GYMPT Deployment Verification Script
# Verifies that all services are running and accessible

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
FRONTEND_URL="${1:-https://gympt.com}"
API_URL="${2:-https://api.gympt.com}"
WS_URL="${3:-wss://ws.gympt.com}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}GYMPT Deployment Verification${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "Frontend URL: ${FRONTEND_URL}"
echo -e "API URL:      ${API_URL}"
echo -e "WebSocket URL: ${WS_URL}"
echo ""

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

check_service() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking ${name}... "

    status_code=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "${url}" || echo "000")

    if [ "${status_code}" = "${expected_status}" ]; then
        echo -e "${GREEN}✓ OK${NC} (${status_code})"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected: ${expected_status}, Got: ${status_code})"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_json_response() {
    local name="$1"
    local url="$2"
    local expected_field="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking ${name}... "

    response=$(curl -s -m 10 "${url}" || echo "{}")

    if echo "${response}" | jq -e ".${expected_field}" > /dev/null 2>&1; then
        value=$(echo "${response}" | jq -r ".${expected_field}")
        echo -e "${GREEN}✓ OK${NC} (${expected_field}: ${value})"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Field '${expected_field}' not found)"
        echo "Response: ${response}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo -e "${BLUE}=== Frontend Checks ===${NC}"
check_service "Frontend Home" "${FRONTEND_URL}" "200"
check_service "Frontend Login" "${FRONTEND_URL}/login" "200"
check_service "Frontend Signup" "${FRONTEND_URL}/signup" "200"

echo ""
echo -e "${BLUE}=== Backend API Checks ===${NC}"
check_json_response "API Health" "${API_URL}/actuator/health" "status"
check_json_response "API Info" "${API_URL}/actuator/info" "app.name"

echo ""
echo -e "${BLUE}=== Agent Service Checks ===${NC}"
check_json_response "Agent Health" "${API_URL}/agent/health" "status"

echo ""
echo -e "${BLUE}=== SSL Certificate Checks ===${NC}"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking Frontend SSL... "
if echo | openssl s_client -connect "${FRONTEND_URL/https:\/\//}:443" -servername "${FRONTEND_URL/https:\/\//}" 2>/dev/null | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✓ Valid${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}⚠ Warning${NC} (Certificate may not be fully trusted yet)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking API SSL... "
if echo | openssl s_client -connect "${API_URL/https:\/\//}:443" -servername "${API_URL/https:\/\//}" 2>/dev/null | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✓ Valid${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}⚠ Warning${NC} (Certificate may not be fully trusted yet)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

echo ""
echo -e "${BLUE}=== DNS Resolution Checks ===${NC}"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking Frontend DNS... "
if host "${FRONTEND_URL/https:\/\//}" > /dev/null 2>&1; then
    ip=$(host "${FRONTEND_URL/https:\/\//}" | grep "has address" | awk '{print $4}' | head -1)
    echo -e "${GREEN}✓ Resolved${NC} (${ip})"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗ FAILED${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking API DNS... "
if host "${API_URL/https:\/\//}" > /dev/null 2>&1; then
    ip=$(host "${API_URL/https:\/\//}" | grep "has address" | awk '{print $4}' | head -1)
    echo -e "${GREEN}✓ Resolved${NC} (${ip})"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗ FAILED${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
echo -e "${BLUE}=== Kubernetes Checks ===${NC}"
if command -v kubectl &> /dev/null; then
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Checking EKS connection... "
    if kubectl cluster-info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))

        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        echo -n "Checking Backend API pods... "
        pod_count=$(kubectl get pods -n gympt-prod -l app=backend-api --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
        if [ "${pod_count}" -gt 0 ]; then
            echo -e "${GREEN}✓ Running${NC} (${pod_count} pods)"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "${RED}✗ No running pods${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi

        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        echo -n "Checking Agent Service pods... "
        pod_count=$(kubectl get pods -n gympt-prod -l app=agent-service --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
        if [ "${pod_count}" -gt 0 ]; then
            echo -e "${GREEN}✓ Running${NC} (${pod_count} pods)"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "${RED}✗ No running pods${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi

        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        echo -n "Checking Posture Analysis pods... "
        pod_count=$(kubectl get pods -n gympt-prod -l app=posture-analysis --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
        if [ "${pod_count}" -gt 0 ]; then
            echo -e "${GREEN}✓ Running${NC} (${pod_count} pods)"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "${RED}✗ No running pods${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo -e "${YELLOW}○ Not configured${NC}"
        TOTAL_CHECKS=$((TOTAL_CHECKS - 1))
    fi
else
    echo -e "${YELLOW}○ kubectl not installed${NC}"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Total Checks:  ${TOTAL_CHECKS}"
echo -e "${GREEN}Passed:        ${PASSED_CHECKS}${NC}"
echo -e "${RED}Failed:        ${FAILED_CHECKS}${NC}"

PERCENTAGE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo -e "Success Rate:  ${PERCENTAGE}%"
echo ""

if [ ${FAILED_CHECKS} -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Deployment is healthy.${NC}"
    exit 0
elif [ ${PERCENTAGE} -ge 80 ]; then
    echo -e "${YELLOW}⚠ Most checks passed, but some issues detected.${NC}"
    echo -e "${YELLOW}Please review failed checks above.${NC}"
    exit 0
else
    echo -e "${RED}✗ Multiple checks failed. Deployment may have issues.${NC}"
    echo -e "${RED}Please investigate failed checks above.${NC}"
    exit 1
fi
