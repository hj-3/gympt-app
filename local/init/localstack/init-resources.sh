#!/bin/bash

# This script runs automatically when LocalStack starts
# It initializes AWS resources for local development

set -e

echo "Initializing LocalStack resources for GYMPT..."

REGION="ap-northeast-2"

# Wait for LocalStack to be ready
sleep 5

# ============================================
# S3 Buckets
# ============================================
echo "Creating S3 buckets..."

awslocal s3 mb s3://gympt-video-local --region $REGION || true
awslocal s3 mb s3://gympt-reports-local --region $REGION || true
awslocal s3 mb s3://gympt-thumbnails-local --region $REGION || true
awslocal s3 mb s3://gympt-exports-local --region $REGION || true

echo "✓ S3 buckets created"

# ============================================
# SQS Queues
# ============================================
echo "Creating SQS queues..."

awslocal sqs create-queue \
    --queue-name gympt-posture-events-local \
    --region $REGION \
    --attributes VisibilityTimeout=300,MessageRetentionPeriod=604800 || true

awslocal sqs create-queue \
    --queue-name gympt-reports-local \
    --region $REGION \
    --attributes VisibilityTimeout=600,MessageRetentionPeriod=1209600 || true

awslocal sqs create-queue \
    --queue-name gympt-notifications-local \
    --region $REGION \
    --attributes VisibilityTimeout=60,MessageRetentionPeriod=345600 || true

awslocal sqs create-queue \
    --queue-name gympt-thumbnails-local \
    --region $REGION \
    --attributes VisibilityTimeout=120,MessageRetentionPeriod=86400 || true

awslocal sqs create-queue \
    --queue-name gympt-wearable-sync-local \
    --region $REGION \
    --attributes VisibilityTimeout=180,MessageRetentionPeriod=259200 || true

awslocal sqs create-queue \
    --queue-name gympt-recommendations-local \
    --region $REGION \
    --attributes VisibilityTimeout=300,MessageRetentionPeriod=604800 || true

awslocal sqs create-queue \
    --queue-name gympt-exports-local \
    --region $REGION \
    --attributes VisibilityTimeout=600,MessageRetentionPeriod=259200 || true

# Create DLQs
awslocal sqs create-queue \
    --queue-name gympt-posture-events-dlq-local \
    --region $REGION || true

awslocal sqs create-queue \
    --queue-name gympt-reports-dlq-local \
    --region $REGION || true

echo "✓ SQS queues created"

# ============================================
# DynamoDB Tables
# ============================================
echo "Creating DynamoDB tables..."

awslocal dynamodb create-table \
    --table-name gympt-events-local \
    --attribute-definitions \
        AttributeName=event_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=event_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --global-secondary-indexes \
        "IndexName=user-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION || true

awslocal dynamodb create-table \
    --table-name gympt-sessions-local \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=user-sessions-index,KeySchema=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION || true

awslocal dynamodb create-table \
    --table-name gympt-posture-data-local \
    --attribute-definitions \
        AttributeName=posture_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=posture_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION || true

echo "✓ DynamoDB tables created"

# ============================================
# SNS Topics
# ============================================
echo "Creating SNS topics..."

awslocal sns create-topic \
    --name gympt-notifications-local \
    --region $REGION || true

awslocal sns create-topic \
    --name gympt-alerts-local \
    --region $REGION || true

echo "✓ SNS topics created"

# ============================================
# EventBridge Event Bus
# ============================================
echo "Creating EventBridge event bus..."

awslocal events create-event-bus \
    --name gympt-events-local \
    --region $REGION || true

# Create event rules
awslocal events put-rule \
    --name gympt-workout-started \
    --event-bus-name gympt-events-local \
    --event-pattern '{"source":["gympt.workouts"],"detail-type":["Workout Started"]}' \
    --region $REGION || true

awslocal events put-rule \
    --name gympt-workout-completed \
    --event-bus-name gympt-events-local \
    --event-pattern '{"source":["gympt.workouts"],"detail-type":["Workout Completed"]}' \
    --region $REGION || true

awslocal events put-rule \
    --name gympt-posture-alert \
    --event-bus-name gympt-events-local \
    --event-pattern '{"source":["gympt.posture"],"detail-type":["Posture Alert"]}' \
    --region $REGION || true

echo "✓ EventBridge event bus and rules created"

# ============================================
# Secrets Manager
# ============================================
echo "Creating secrets..."

awslocal secretsmanager create-secret \
    --name gympt/local/database \
    --secret-string '{"username":"gympt_user","password":"gympt_local_pass","host":"postgres","port":"5432","dbname":"gympt"}' \
    --region $REGION || true

awslocal secretsmanager create-secret \
    --name gympt/local/redis \
    --secret-string '{"host":"redis","port":"6379","password":""}' \
    --region $REGION || true

awslocal secretsmanager create-secret \
    --name gympt/local/jwt \
    --secret-string '{"secret":"local-jwt-secret-key-change-in-production"}' \
    --region $REGION || true

echo "✓ Secrets created"

# ============================================
# Kinesis Video Streams (Note: Limited support in LocalStack)
# ============================================
echo "Note: Kinesis Video Streams has limited support in LocalStack"
echo "For video streaming, use actual AWS KVS in dev/prod environments"

echo ""
echo "═══════════════════════════════════════"
echo "LocalStack initialization complete! ✓"
echo "═══════════════════════════════════════"
echo ""
echo "Resources created:"
echo "  • S3 buckets: 4"
echo "  • SQS queues: 7 (+ 2 DLQs)"
echo "  • DynamoDB tables: 3"
echo "  • SNS topics: 2"
echo "  • EventBridge: 1 bus + 3 rules"
echo "  • Secrets: 3"
echo ""
