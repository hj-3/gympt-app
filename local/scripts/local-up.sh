#!/bin/bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   GYMPT Local Environment Startup     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Change to local directory
cd "$(dirname "$0")/.."

# Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check .env file
echo -e "\n${YELLOW}[2/6] Checking environment configuration...${NC}"
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Copying .env.example to .env...${NC}"
    cp ../.env.example ../.env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}Please review and update .env file if needed${NC}"
fi

# Stop existing containers
echo -e "\n${YELLOW}[3/6] Stopping existing containers...${NC}"
docker compose down -v 2>/dev/null || true
echo -e "${GREEN}✓ Existing containers stopped${NC}"

# Start infrastructure services
echo -e "\n${YELLOW}[4/6] Starting infrastructure services...${NC}"
docker compose up -d postgres redis localstack dynamodb-local dynamodb-admin

# Wait for services to be healthy
echo -e "\n${YELLOW}[5/6] Waiting for services to be ready...${NC}"

echo -n "  • PostgreSQL..."
timeout=60
counter=0
until docker compose exec -T postgres pg_isready -U gympt_user -d gympt &> /dev/null; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo -e " ${RED}✗ Timeout${NC}"
        exit 1
    fi
done
echo -e " ${GREEN}✓${NC}"

echo -n "  • Redis..."
counter=0
until docker compose exec -T redis redis-cli ping &> /dev/null; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo -e " ${RED}✗ Timeout${NC}"
        exit 1
    fi
done
echo -e " ${GREEN}✓${NC}"

echo -n "  • LocalStack..."
counter=0
until curl -s http://localhost:4566/_localstack/health | grep -q "running"; do
    sleep 3
    counter=$((counter + 3))
    if [ $counter -ge $timeout ]; then
        echo -e " ${RED}✗ Timeout${NC}"
        exit 1
    fi
done
echo -e " ${GREEN}✓${NC}"

# Initialize LocalStack resources
echo -e "\n${YELLOW}[6/6] Initializing LocalStack resources...${NC}"
./scripts/init-localstack.sh

echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Local Infrastructure Ready! 🚀       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo -e ""
echo -e "${BLUE}Infrastructure Services:${NC}"
echo -e "  PostgreSQL:         ${GREEN}localhost:5432${NC} (user: gympt_user, db: gympt)"
echo -e "  Redis:              ${GREEN}localhost:6379${NC}"
echo -e "  DynamoDB Local:     ${GREEN}http://localhost:8000${NC}"
echo -e "  DynamoDB Admin UI:  ${GREEN}http://localhost:8001${NC}"
echo -e "  LocalStack:         ${GREEN}http://localhost:4566${NC}"
echo -e ""
echo -e "${YELLOW}Note: Application services require Dockerfiles. Build them separately once implemented.${NC}"
echo -e ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  View logs:          ${GREEN}./scripts/local-logs.sh${NC}"
echo -e "  Stop services:      ${GREEN}./scripts/local-down.sh${NC}"
echo -e "  Reset environment:  ${GREEN}./scripts/local-reset.sh${NC}"
echo -e "  Seed test data:     ${GREEN}./scripts/local-seed.sh${NC}"
echo -e ""
echo -e "${YELLOW}Optional Observability:${NC}"
echo -e "  Start monitoring:   ${GREEN}docker compose -f docker-compose.observability.yml up -d${NC}"
echo -e "  Prometheus:         ${GREEN}http://localhost:9090${NC}"
echo -e "  Grafana:            ${GREEN}http://localhost:3010${NC} (admin/admin123)"
echo -e "  Jaeger:             ${GREEN}http://localhost:16686${NC}"
echo ""
