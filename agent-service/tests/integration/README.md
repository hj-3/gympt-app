# Agent Service - Integration Tests

## Structure

```
integration/
├── test_api_endpoints.py       # FastAPI endpoint tests
├── test_redis_integration.py   # Redis caching tests
└── test_dynamo_integration.py  # DynamoDB persistence tests
```

## Test Dependencies

- Redis (TestContainers or Docker)
- DynamoDB Local or moto

## Running

```bash
# Start test dependencies
docker compose -f docker-compose.test.yml up -d

# Run tests
pytest tests/integration/ -v

# Cleanup
docker compose -f docker-compose.test.yml down
```
