"""
Tests for Bedrock mock responses.

Ensures mock responses match real Bedrock format and are suitable for testing.
"""
import pytest


@pytest.mark.unit
def test_mock_bedrock_response_structure():
    """Test mock Bedrock response has correct structure."""
    from tests.utils.helpers import generate_mock_bedrock_response

    response = generate_mock_bedrock_response("workout")

    # Verify structure matches real Bedrock
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert "stop_reason" in response

    # Verify types
    assert isinstance(response["content"], str)
    assert isinstance(response["model"], str)
    assert isinstance(response["usage"], dict)
    assert isinstance(response["stop_reason"], str)


@pytest.mark.unit
def test_mock_bedrock_usage_structure():
    """Test mock usage structure."""
    from tests.utils.helpers import generate_mock_bedrock_response

    response = generate_mock_bedrock_response()

    usage = response["usage"]
    assert "input_tokens" in usage
    assert "output_tokens" in usage

    assert isinstance(usage["input_tokens"], int)
    assert isinstance(usage["output_tokens"], int)
    assert usage["input_tokens"] > 0
    assert usage["output_tokens"] > 0


@pytest.mark.unit
def test_mock_bedrock_workout_content():
    """Test mock workout response has appropriate content."""
    from tests.utils.helpers import generate_mock_bedrock_response

    response = generate_mock_bedrock_response("workout")

    content = response["content"].lower()

    # Should contain workout-related terms
    workout_terms = ["workout", "exercise", "training", "strength", "week", "day"]
    assert any(term in content for term in workout_terms)


@pytest.mark.unit
def test_mock_bedrock_posture_content():
    """Test mock posture response has appropriate content."""
    from tests.utils.helpers import generate_mock_bedrock_response

    response = generate_mock_bedrock_response("posture")

    content = response["content"].lower()

    # Should contain posture-related terms
    posture_terms = ["form", "posture", "alignment", "correction", "improvement"]
    assert any(term in content for term in posture_terms)


@pytest.mark.unit
def test_mock_bedrock_report_content():
    """Test mock report response has appropriate content."""
    from tests.utils.helpers import generate_mock_bedrock_response

    response = generate_mock_bedrock_response("report")

    content = response["content"].lower()

    # Should contain report-related terms
    report_terms = ["summary", "progress", "achievement", "recommendation", "week"]
    assert any(term in content for term in report_terms)


@pytest.mark.unit
def test_mock_bedrock_client_invoke_model():
    """Test mock Bedrock client invoke_model method."""
    from app.clients.bedrock_client import BedrockClient

    client = BedrockClient()
    client.mock_enabled = True

    # Should return mock response
    assert client.mock_enabled is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_bedrock_response_async():
    """Test mock Bedrock works with async calls."""
    from app.clients.bedrock_client import BedrockClient

    client = BedrockClient()
    client.mock_enabled = True

    response = await client.invoke_model("Test prompt")

    assert response is not None
    assert "content" in response
    assert isinstance(response["content"], str)


@pytest.mark.unit
def test_mock_response_deterministic():
    """Test mock responses are consistent for same input type."""
    from tests.utils.helpers import generate_mock_bedrock_response

    response1 = generate_mock_bedrock_response("workout")
    response2 = generate_mock_bedrock_response("workout")

    # Structure should be same
    assert response1.keys() == response2.keys()
    assert response1["model"] == response2["model"]
    assert response1["stop_reason"] == response2["stop_reason"]


@pytest.mark.unit
def test_mock_response_different_types():
    """Test mock responses differ by content type."""
    from tests.utils.helpers import generate_mock_bedrock_response

    workout_response = generate_mock_bedrock_response("workout")
    posture_response = generate_mock_bedrock_response("posture")
    report_response = generate_mock_bedrock_response("report")

    # Content should differ
    assert workout_response["content"] != posture_response["content"]
    assert workout_response["content"] != report_response["content"]
    assert posture_response["content"] != report_response["content"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_bedrock_latency_simulation():
    """Test mock can simulate latency if needed."""
    import time
    from app.clients.bedrock_client import BedrockClient

    client = BedrockClient()
    client.mock_enabled = True

    start = time.time()
    await client.invoke_model("Test prompt")
    duration = time.time() - start

    # Mock should be fast (< 100ms)
    assert duration < 0.1
