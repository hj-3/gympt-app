#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping GYMPT local environment...${NC}"

cd "$(dirname "$0")/.."

# Stop all services
docker compose down

# Optionally stop observability stack
if docker compose -f docker-compose.observability.yml ps &> /dev/null; then
    echo -e "${YELLOW}Stopping observability stack...${NC}"
    docker compose -f docker-compose.observability.yml down
fi

echo -e "${GREEN}✓ All services stopped${NC}"
echo -e "${YELLOW}Note: Data volumes are preserved. Use local-reset.sh to remove all data.${NC}"
