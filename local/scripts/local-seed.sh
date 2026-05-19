#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Seeding test data for GYMPT local environment...${NC}"

cd "$(dirname "$0")/.."

# Wait for backend API to be ready
echo -e "${YELLOW}Waiting for backend API...${NC}"
timeout=120
counter=0
until curl -s http://localhost:8080/actuator/health | grep -q "UP"; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}Error: Backend API not available${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Backend API ready${NC}"

# Seed test users
echo -e "\n${YELLOW}Creating test users...${NC}"
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gympt.com",
    "password": "test123",
    "name": "Test User",
    "age": 30,
    "gender": "M",
    "fitness_level": "INTERMEDIATE"
  }' || echo "User may already exist"

curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@gympt.com",
    "password": "admin123",
    "name": "Admin User",
    "age": 35,
    "gender": "F",
    "fitness_level": "ADVANCED"
  }' || echo "User may already exist"

echo -e "${GREEN}✓ Test users created${NC}"

# Seed test data in PostgreSQL
echo -e "\n${YELLOW}Seeding PostgreSQL test data...${NC}"
docker-compose exec -T postgres psql -U gympt_user -d gympt <<EOF
-- Insert sample workout types if not exists
INSERT INTO workout_types (id, name, description, category, created_at)
VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 'Push-ups', 'Upper body strength', 'STRENGTH', NOW()),
  ('550e8400-e29b-41d4-a716-446655440002', 'Squats', 'Lower body strength', 'STRENGTH', NOW()),
  ('550e8400-e29b-41d4-a716-446655440003', 'Running', 'Cardio exercise', 'CARDIO', NOW())
ON CONFLICT (id) DO NOTHING;
EOF

echo -e "${GREEN}✓ PostgreSQL seeded${NC}"

# Seed test data in DynamoDB
echo -e "\n${YELLOW}Seeding DynamoDB test data...${NC}"
aws --endpoint-url=http://localhost:4566 dynamodb put-item \
  --table-name gympt-events-dev \
  --item '{
    "event_id": {"S": "test-event-001"},
    "timestamp": {"N": "1716048000000"},
    "event_type": {"S": "workout_started"},
    "user_id": {"S": "test-user-001"},
    "data": {"S": "{\"workout_type\": \"push-ups\"}"}
  }' \
  --region ap-northeast-2 || echo "Event may already exist"

echo -e "${GREEN}✓ DynamoDB seeded${NC}"

echo -e "\n${GREEN}╔═══════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Test Data Seeding Complete! ✓   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Test Credentials:${NC}"
echo -e "  Email: test@gympt.com"
echo -e "  Password: test123"
echo -e ""
echo -e "  Email: admin@gympt.com"
echo -e "  Password: admin123"
