#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GYMPT Local Infrastructure Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Navigate to compose directory
cd "$(dirname "$0")/../compose"

# Check if .env file exists
if [ ! -f "../../.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Copying .env.example to .env...${NC}"
    cp ../../.env.example ../../.env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}Please update .env file with your configuration${NC}"
fi

# Stop existing containers
echo -e "\n${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Start infrastructure services only
echo -e "\n${YELLOW}Starting infrastructure services...${NC}"
docker-compose up -d postgres redis localstack prometheus grafana

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"

echo -n "Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U gympt_user -d gympt &> /dev/null; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"

echo -n "Waiting for Redis..."
until docker-compose exec -T redis redis-cli ping &> /dev/null; do
    echo -n "."
    sleep 1
done
echo -e " ${GREEN}✓${NC}"

echo -n "Waiting for LocalStack..."
until curl -s http://localhost:4566/_localstack/health | grep -q "running"; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✓${NC}"

# Initialize LocalStack resources
echo -e "\n${YELLOW}Initializing LocalStack resources...${NC}"
./init-localstack.sh

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Infrastructure is ready!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\nService URLs:"
echo -e "  PostgreSQL:   ${GREEN}localhost:5432${NC}"
echo -e "  Redis:        ${GREEN}localhost:6379${NC}"
echo -e "  LocalStack:   ${GREEN}http://localhost:4566${NC}"
echo -e "  Prometheus:   ${GREEN}http://localhost:9090${NC}"
echo -e "  Grafana:      ${GREEN}http://localhost:3001${NC} (admin/admin)"

echo -e "\nTo start application services, run:"
echo -e "  ${YELLOW}docker-compose up -d backend-api agent-service posture-analysis-service${NC}"

echo -e "\nTo stop all services, run:"
echo -e "  ${YELLOW}docker-compose down${NC}"
