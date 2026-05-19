#!/bin/bash

set -e

# LocalStack endpoint
ENDPOINT="http://localhost:4566"
REGION="ap-northeast-2"

echo "Initializing LocalStack resources..."

# Create S3 Buckets
echo "Creating S3 buckets..."
aws --endpoint-url=$ENDPOINT s3 mb s3://gympt-video-dev --region $REGION || true
aws --endpoint-url=$ENDPOINT s3 mb s3://gympt-reports-dev --region $REGION || true
echo "✓ S3 buckets created"

# Create SQS Queues
echo "Creating SQS queues..."
aws --endpoint-url=$ENDPOINT sqs create-queue \
    --queue-name gympt-posture-events-dev \
    --region $REGION || true

aws --endpoint-url=$ENDPOINT sqs create-queue \
    --queue-name gympt-reports-dev \
    --region $REGION || true
echo "✓ SQS queues created"

# Create DynamoDB Tables
echo "Creating DynamoDB tables..."
aws --endpoint-url=$ENDPOINT dynamodb create-table \
    --table-name gympt-events-dev \
    --attribute-definitions \
        AttributeName=event_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=event_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION || true
echo "✓ DynamoDB tables created"

# Create EventBridge Event Bus
echo "Creating EventBridge event bus..."
aws --endpoint-url=$ENDPOINT events create-event-bus \
    --name gympt-events-dev \
    --region $REGION || true
echo "✓ EventBridge event bus created"

# Create Kinesis Video Stream (placeholder - KVS doesn't run in LocalStack)
echo "Note: Kinesis Video Streams requires actual AWS for testing"

echo ""
echo "LocalStack initialization complete!"
