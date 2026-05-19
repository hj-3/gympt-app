from app.clients.bedrock_client import bedrock_client
from app.clients.redis_client import redis_client
from app.clients.dynamodb_client import dynamodb_client
from app.clients.sqs_client import sqs_client
from app.clients.backend_client import backend_client

__all__ = [
    "bedrock_client",
    "redis_client",
    "dynamodb_client",
    "sqs_client",
    "backend_client"
]
