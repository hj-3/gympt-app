#!/bin/bash

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}⚠️  WARNING: This will delete ALL local data!${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  - PostgreSQL databases"
echo -e "  - Redis data"
echo -e "  - DynamoDB data"
echo -e "  - LocalStack data"
echo -e "  - Prometheus metrics"
echo -e "  - Grafana dashboards"
echo ""
read -p "Are you sure? (type 'yes' to confirm): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${GREEN}Cancelled.${NC}"
    exit 0
fi

cd "$(dirname "$0")/.."

echo -e "${YELLOW}Stopping all containers...${NC}"
docker compose down -v
docker compose -f docker-compose.observability.yml down -v 2>/dev/null || true

echo -e "${YELLOW}Removing volumes...${NC}"
docker volume rm gympt_postgres_data 2>/dev/null || true
docker volume rm gympt_redis_data 2>/dev/null || true
docker volume rm gympt_dynamodb_data 2>/dev/null || true
docker volume rm gympt_localstack_data 2>/dev/null || true
docker volume rm gympt_prometheus_data 2>/dev/null || true
docker volume rm gympt_grafana_data 2>/dev/null || true
docker volume rm gympt_loki_data 2>/dev/null || true
docker volume rm gympt_jaeger_data 2>/dev/null || true

echo -e "${YELLOW}Removing network...${NC}"
docker network rm gympt-network 2>/dev/null || true

echo -e "${GREEN}✓ Local environment reset complete${NC}"
echo -e "${YELLOW}Run ./scripts/local-up.sh to start fresh${NC}"
