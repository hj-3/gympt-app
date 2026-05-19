import pytest
from unittest.mock import patch, MagicMock
from app.clients.bedrock_client import BedrockClient


@pytest.mark.asyncio
async def test_mock_response_workout():
    """Test mock response for workout recommendation."""
    client = BedrockClient()
    client.mock_enabled = True
    
    response = await client.invoke_model("Generate a workout plan")
    
    assert "workout" in response["content"].lower() or "strength" in response["content"].lower()
    assert response["model"] == "mock-model"
    assert "usage" in response


@pytest.mark.asyncio
async def test_mock_response_posture():
    """Test mock response for posture feedback."""
    client = BedrockClient()
    client.mock_enabled = True
    
    response = await client.invoke_model("Analyze posture for squat")
    
    assert "posture" in response["content"].lower() or "form" in response["content"].lower()
    assert response["stop_reason"] == "end_turn"


@pytest.mark.asyncio
async def test_mock_agent_response():
    """Test mock agent invocation."""
    client = BedrockClient()
    client.mock_enabled = True
    
    response = await client.invoke_agent(
        session_id="test-session",
        input_text="Hello agent"
    )
    
    assert "completion" in response
    assert response["session_id"] == "mock-session"


@pytest.mark.asyncio
async def test_mock_knowledge_base():
    """Test mock knowledge base retrieval."""
    client = BedrockClient()
    client.mock_enabled = True
    
    response = await client.retrieve_from_knowledge_base("exercise technique")
    
    assert response["count"] > 0
    assert len(response["results"]) > 0
    assert "content" in response["results"][0]
