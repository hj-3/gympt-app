from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)

# Bedrock metrics
bedrock_requests_total = Counter(
    'bedrock_requests_total',
    'Total number of Bedrock API requests',
    ['model_id', 'endpoint']
)

bedrock_request_duration_seconds = Histogram(
    'bedrock_request_duration_seconds',
    'Duration of Bedrock API requests in seconds',
    ['model_id', 'endpoint']
)

bedrock_tokens_used_total = Counter(
    'bedrock_tokens_used_total',
    'Total number of tokens used',
    ['model_id', 'token_type']
)

bedrock_errors_total = Counter(
    'bedrock_errors_total',
    'Total number of Bedrock errors',
    ['model_id', 'error_type']
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['endpoint']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['endpoint']
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['operation']  # get, set, delete
)

# DynamoDB metrics
dynamodb_writes_total = Counter(
    'dynamodb_writes_total',
    'Total number of DynamoDB write operations',
    ['table_name', 'interaction_type']
)

dynamodb_errors_total = Counter(
    'dynamodb_errors_total',
    'Total number of DynamoDB errors',
    ['table_name', 'error_type']
)

dynamodb_operation_duration_seconds = Histogram(
    'dynamodb_operation_duration_seconds',
    'Duration of DynamoDB operations in seconds',
    ['table_name', 'operation']
)

# SQS metrics
sqs_messages_published_total = Counter(
    'sqs_messages_published_total',
    'Total number of SQS messages published',
    ['queue_name', 'task_type']
)

sqs_publish_errors_total = Counter(
    'sqs_publish_errors_total',
    'Total number of SQS publish errors',
    ['queue_name', 'error_type']
)

# Backend API metrics
backend_api_requests_total = Counter(
    'backend_api_requests_total',
    'Total number of Backend API requests',
    ['endpoint', 'method']
)

backend_api_errors_total = Counter(
    'backend_api_errors_total',
    'Total number of Backend API errors',
    ['endpoint', 'status_code']
)

backend_api_duration_seconds = Histogram(
    'backend_api_duration_seconds',
    'Duration of Backend API requests in seconds',
    ['endpoint', 'method']
)

# Agent service metrics
agent_interactions_total = Counter(
    'agent_interactions_total',
    'Total number of agent interactions',
    ['interaction_type', 'status']  # status: success, error
)

agent_interaction_duration_seconds = Histogram(
    'agent_interaction_duration_seconds',
    'Duration of agent interactions in seconds',
    ['interaction_type']
)

# Application metrics
active_requests = Gauge(
    'active_requests',
    'Number of active requests being processed'
)

logger.info("Prometheus metrics initialized")
