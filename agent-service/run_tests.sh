#!/bin/bash

# GYMPT Agent Service - Test Runner Script
# Quick commands to run different test categories

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}GYMPT Agent Service Test Runner${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Parse command line arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        echo -e "${GREEN}Running Unit Tests...${NC}"
        pytest -m unit -v --cov=app --cov-report=term-missing
        ;;

    integration)
        echo -e "${GREEN}Running Integration Tests...${NC}"
        echo -e "${YELLOW}Note: Requires Redis, DynamoDB (start with: cd tests && docker-compose -f docker-compose.test.yml up -d)${NC}"
        pytest -m integration -v
        ;;

    e2e)
        echo -e "${GREEN}Running End-to-End Tests...${NC}"
        pytest -m e2e -v
        ;;

    smoke)
        echo -e "${GREEN}Running Smoke Tests...${NC}"
        pytest -m smoke -v
        ;;

    performance)
        echo -e "${GREEN}Running Performance Tests...${NC}"
        echo -e "${YELLOW}Note: These tests are slow (may take several minutes)${NC}"
        pytest -m performance -v
        ;;

    regression)
        echo -e "${GREEN}Running Regression Tests...${NC}"
        pytest -m regression -v
        ;;

    api)
        echo -e "${GREEN}Running API Tests...${NC}"
        pytest tests/api/ -v
        ;;

    coverage)
        echo -e "${GREEN}Running All Tests with Coverage Report...${NC}"
        pytest --cov=app --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    fast)
        echo -e "${GREEN}Running Fast Tests Only (Unit + Smoke)...${NC}"
        pytest -m "unit or smoke" -v
        ;;

    parallel)
        echo -e "${GREEN}Running Tests in Parallel...${NC}"
        pytest -n auto -v
        ;;

    all)
        echo -e "${GREEN}Running All Tests...${NC}"
        pytest -v
        ;;

    help|--help|-h)
        echo "Usage: ./run_tests.sh [TEST_TYPE]"
        echo ""
        echo "Test Types:"
        echo "  unit         - Unit tests (fast, no external dependencies)"
        echo "  integration  - Integration tests (requires Docker services)"
        echo "  e2e          - End-to-end tests"
        echo "  smoke        - Smoke tests (critical paths)"
        echo "  performance  - Performance tests (slow)"
        echo "  regression   - Regression tests"
        echo "  api          - API endpoint tests"
        echo "  coverage     - All tests with coverage report"
        echo "  fast         - Unit + smoke tests only"
        echo "  parallel     - All tests in parallel"
        echo "  all          - All tests (default)"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh unit"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh fast"
        exit 0
        ;;

    *)
        echo -e "${YELLOW}Unknown test type: $TEST_TYPE${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Tests completed${NC}"
