# Agent Service - Unit Tests

## Structure

```
unit/
├── test_bedrock_client.py      # Bedrock client tests (mocked)
├── test_agent_service.py       # Agent orchestration logic
├── test_context_manager.py     # Context management
└── test_prompt_builder.py      # Prompt construction
```

## Mocking Bedrock

Use `moto` or custom mocks:

```python
@pytest.fixture
def mock_bedrock():
    with patch('boto3.client') as mock:
        mock.return_value.invoke_model.return_value = {
            'body': StreamingBody(
                io.BytesIO(b'{"completion":"Test response"}'),
                100
            )
        }
        yield mock
```

## Running

```bash
pytest tests/unit/ -v --cov=app.services
```
