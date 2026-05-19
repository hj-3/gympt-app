#!/bin/bash
# ============================================
# DynamoDB Local - Create Tables Script
# ============================================
# Creates all DynamoDB tables required for GYMPT local environment
# ============================================

set -e

DYNAMODB_ENDPOINT="http://localhost:8000"
AWS_REGION="ap-northeast-2"

echo "========================================"
echo "Creating DynamoDB Tables for GYMPT Local"
echo "========================================"

# Wait for DynamoDB Local to be ready
echo "Waiting for DynamoDB Local to be ready..."
until curl -s "${DYNAMODB_ENDPOINT}" > /dev/null 2>&1; do
  echo "  DynamoDB Local is unavailable - waiting..."
  sleep 2
done
echo "DynamoDB Local is ready!"

# Configure AWS CLI to use local endpoint
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=${AWS_REGION}

# ============================================
# Table 1: Workout Sessions
# ============================================
echo ""
echo "Creating table: gympt-workout-sessions-local"
aws dynamodb create-table \
  --endpoint-url ${DYNAMODB_ENDPOINT} \
  --table-name gympt-workout-sessions-local \
  --attribute-definitions \
    AttributeName=sessionId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
    AttributeName=startTime,AttributeType=S \
  --key-schema \
    AttributeName=sessionId,KeyType=HASH \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"UserIdIndex\",
        \"KeySchema\": [
          {\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},
          {\"AttributeName\":\"startTime\",\"KeyType\":\"RANGE\"}
        ],
        \"Projection\": {\"ProjectionType\":\"ALL\"},
        \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
      }
    ]" \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  || echo "  Table already exists or creation failed"

# ============================================
# Table 2: Posture Events
# ============================================
echo ""
echo "Creating table: gympt-posture-events-local"
aws dynamodb create-table \
  --endpoint-url ${DYNAMODB_ENDPOINT} \
  --table-name gympt-posture-events-local \
  --attribute-definitions \
    AttributeName=eventId,AttributeType=S \
    AttributeName=sessionId,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=eventId,KeyType=HASH \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"SessionIdIndex\",
        \"KeySchema\": [
          {\"AttributeName\":\"sessionId\",\"KeyType\":\"HASH\"},
          {\"AttributeName\":\"timestamp\",\"KeyType\":\"RANGE\"}
        ],
        \"Projection\": {\"ProjectionType\":\"ALL\"},
        \"ProvisionedThroughput\": {\"ReadCapacityUnits\":10,\"WriteCapacityUnits\":10}
      }
    ]" \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10 \
  || echo "  Table already exists or creation failed"

# ============================================
# Table 3: Wearable Events
# ============================================
echo ""
echo "Creating table: gympt-wearable-events-local"
aws dynamodb create-table \
  --endpoint-url ${DYNAMODB_ENDPOINT} \
  --table-name gympt-wearable-events-local \
  --attribute-definitions \
    AttributeName=eventId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=eventId,KeyType=HASH \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"UserIdIndex\",
        \"KeySchema\": [
          {\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},
          {\"AttributeName\":\"timestamp\",\"KeyType\":\"RANGE\"}
        ],
        \"Projection\": {\"ProjectionType\":\"ALL\"},
        \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
      }
    ]" \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  || echo "  Table already exists or creation failed"

# ============================================
# Table 4: Agent Interactions
# ============================================
echo ""
echo "Creating table: gympt-agent-interactions-local"
aws dynamodb create-table \
  --endpoint-url ${DYNAMODB_ENDPOINT} \
  --table-name gympt-agent-interactions-local \
  --attribute-definitions \
    AttributeName=interactionId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=interactionId,KeyType=HASH \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"UserIdIndex\",
        \"KeySchema\": [
          {\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},
          {\"AttributeName\":\"timestamp\",\"KeyType\":\"RANGE\"}
        ],
        \"Projection\": {\"ProjectionType\":\"ALL\"},
        \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
      }
    ]" \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  || echo "  Table already exists or creation failed"

# ============================================
# Verify Tables
# ============================================
echo ""
echo "========================================"
echo "Verifying created tables..."
echo "========================================"
aws dynamodb list-tables \
  --endpoint-url ${DYNAMODB_ENDPOINT} \
  --output table

echo ""
echo "========================================"
echo "DynamoDB tables created successfully!"
echo "========================================"
echo ""
echo "Access DynamoDB Admin UI: http://localhost:8001"
echo ""
