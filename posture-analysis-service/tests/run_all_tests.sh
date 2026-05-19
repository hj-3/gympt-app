#!/bin/bash

# GYMPT Posture Analysis Service - Test Runner
# Runs comprehensive test suite with different configurations

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=80
TEST_DIR="tests"
REPORT_DIR="test-reports"

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}GYMPT Posture Analysis Test Suite${NC}"
echo -e "${BLUE}=======================================${NC}\n"

# Create report directory
mkdir -p $REPORT_DIR

# Check if dependencies are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found. Please install: pip install -r requirements.txt${NC}"
    exit 1
fi

# Check services
echo -e "${YELLOW}Checking required services...${NC}"

if ! nc -z localhost 6379 2>/dev/null; then
    echo -e "${YELLOW}Warning: Redis not running on localhost:6379${NC}"
    echo -e "${YELLOW}Some integration tests may fail. Start Redis: docker run -d -p 6379:6379 redis:7-alpine${NC}"
fi

# Run unit tests
echo -e "\n${BLUE}Running Unit Tests...${NC}"
pytest tests/unit/ \
    -v \
    -m unit \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:$REPORT_DIR/coverage-unit \
    --junit-xml=$REPORT_DIR/junit-unit.xml \
    || { echo -e "${RED}Unit tests failed${NC}"; exit 1; }

echo -e "${GREEN}✓ Unit tests passed${NC}\n"

# Run WebSocket tests
echo -e "${BLUE}Running WebSocket Tests...${NC}"
pytest tests/websocket/ \
    -v \
    -m websocket \
    --junit-xml=$REPORT_DIR/junit-websocket.xml \
    || { echo -e "${RED}WebSocket tests failed${NC}"; exit 1; }

echo -e "${GREEN}✓ WebSocket tests passed${NC}\n"

# Run integration tests
echo -e "${BLUE}Running Integration Tests...${NC}"
pytest tests/integration/ \
    -v \
    -m integration \
    --junit-xml=$REPORT_DIR/junit-integration.xml \
    || { echo -e "${YELLOW}Warning: Some integration tests failed${NC}"; }

echo -e "${GREEN}✓ Integration tests completed${NC}\n"

# Run E2E tests
echo -e "${BLUE}Running E2E Tests...${NC}"
pytest tests/e2e/ \
    -v \
    -m e2e \
    --junit-xml=$REPORT_DIR/junit-e2e.xml \
    || { echo -e "${YELLOW}Warning: Some E2E tests failed${NC}"; }

echo -e "${GREEN}✓ E2E tests completed${NC}\n"

# Run performance tests (optional)
if [ "$RUN_PERFORMANCE" = "true" ]; then
    echo -e "${BLUE}Running Performance Tests...${NC}"
    pytest tests/performance/ \
        -v \
        -m performance \
        --junit-xml=$REPORT_DIR/junit-performance.xml \
        || { echo -e "${YELLOW}Warning: Some performance tests failed${NC}"; }

    echo -e "${GREEN}✓ Performance tests completed${NC}\n"
else
    echo -e "${YELLOW}Skipping performance tests (set RUN_PERFORMANCE=true to run)${NC}\n"
fi

# Run GPU tests (optional)
if [ "$RUN_GPU_TESTS" = "true" ]; then
    echo -e "${BLUE}Running GPU Tests...${NC}"
    pytest tests/gpu/ \
        -v \
        -m gpu \
        --junit-xml=$REPORT_DIR/junit-gpu.xml \
        || { echo -e "${YELLOW}Warning: GPU tests skipped or failed${NC}"; }

    echo -e "${GREEN}✓ GPU tests completed${NC}\n"
else
    echo -e "${YELLOW}Skipping GPU tests (set RUN_GPU_TESTS=true to run)${NC}\n"
fi

# Generate comprehensive coverage report
echo -e "${BLUE}Generating Coverage Report...${NC}"
pytest tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:$REPORT_DIR/coverage-all \
    --cov-report=xml:$REPORT_DIR/coverage.xml \
    --cov-fail-under=$COVERAGE_THRESHOLD \
    -m "not slow and not gpu" \
    --quiet \
    || { echo -e "${RED}Coverage threshold not met (required: ${COVERAGE_THRESHOLD}%)${NC}"; exit 1; }

echo -e "${GREEN}✓ Coverage report generated${NC}\n"

# Summary
echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}All Test Suites Completed!${NC}"
echo -e "${BLUE}=======================================${NC}\n"

echo -e "Test reports available in: ${BLUE}$REPORT_DIR/${NC}"
echo -e "Coverage report: ${BLUE}$REPORT_DIR/coverage-all/index.html${NC}\n"

# Coverage summary
echo -e "${YELLOW}Coverage Summary:${NC}"
coverage report --skip-covered | tail -n 3

exit 0
