import boto3
import json
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """Amazon Bedrock client wrapper."""
    
    def __init__(self):
        self.region = settings.bedrock_region
        self.model_id = settings.bedrock_model_id
        self.mock_enabled = settings.enable_bedrock_mock
        
        if not self.mock_enabled:
            session_kwargs = {"region_name": self.region}
            if settings.aws_access_key_id:
                session_kwargs.update({
                    "aws_access_key_id": settings.aws_access_key_id,
                    "aws_secret_access_key": settings.aws_secret_access_key
                })
            
            self.runtime_client = boto3.client(
                "bedrock-runtime",
                **session_kwargs
            )
            
            if settings.bedrock_agent_id:
                self.agent_client = boto3.client(
                    "bedrock-agent-runtime",
                    **session_kwargs
                )
    
    async def invoke_model(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke Bedrock model with prompt."""
        
        if self.mock_enabled:
            return self._mock_response(prompt)
        
        try:
            # Prepare request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            if system:
                body["system"] = system
            
            response = self.runtime_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                "content": response_body['content'][0]['text'],
                "model": self.model_id,
                "usage": response_body.get('usage', {}),
                "stop_reason": response_body.get('stop_reason')
            }
            
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            raise
    
    async def invoke_agent(
        self,
        session_id: str,
        input_text: str,
        enable_trace: bool = False
    ) -> Dict[str, Any]:
        """Invoke Bedrock Agent."""

        if self.mock_enabled or not settings.bedrock_agent_id:
            logger.warning("Using mock agent response - Bedrock Agent not configured")
            return self._mock_agent_response(input_text)

        try:
            logger.info(f"Invoking Bedrock Agent: agentId={settings.bedrock_agent_id}, "
                       f"agentAliasId={settings.bedrock_agent_alias_id}, "
                       f"sessionId={session_id}, region={self.region}")

            response = self.agent_client.invoke_agent(
                agentId=settings.bedrock_agent_id,
                agentAliasId=settings.bedrock_agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=enable_trace
            )

            logger.info(f"Bedrock Agent response received, processing stream...")

            # Process streaming response
            completion = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')

            logger.info(f"Bedrock Agent completion length: {len(completion)} characters")

            return {
                "completion": completion,
                "session_id": session_id,
                "trace": response.get('trace') if enable_trace else None
            }

        except Exception as e:
            logger.error(f"Bedrock Agent invocation failed: {e}", exc_info=True)
            raise
    
    async def retrieve_from_knowledge_base(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Retrieve information from Bedrock Knowledge Base."""
        
        if self.mock_enabled or not settings.bedrock_knowledge_base_id:
            return self._mock_kb_response(query)
        
        try:
            response = self.agent_client.retrieve(
                knowledgeBaseId=settings.bedrock_knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for item in response.get('retrievalResults', []):
                results.append({
                    "content": item['content']['text'],
                    "score": item.get('score', 0.0),
                    "location": item.get('location', {})
                })
            
            return {
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Knowledge Base retrieval failed: {e}")
            raise
    
    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        """Generate mock response for local testing."""
        logger.info("Using mock Bedrock response")
        
        # Simple mock based on prompt keywords
        if "workout" in prompt.lower():
            content = """Based on your fitness level and goals, I recommend:

1. **Strength Training** (3x per week)
   - Squats: 3 sets x 8-10 reps
   - Bench Press: 3 sets x 8-10 reps
   - Deadlifts: 3 sets x 6-8 reps

2. **Cardio** (2x per week)
   - 30 minutes moderate intensity

3. **Rest & Recovery**
   - 2 days complete rest
   - Adequate sleep and nutrition"""
        
        elif "posture" in prompt.lower():
            content = """Posture Analysis Feedback:

✓ **Good Form:**
- Upper body alignment is correct
- Core engagement maintained

⚠ **Areas for Improvement:**
- Knee tracking: slight valgus detected
- Depth: aim for parallel or below

**Recommendations:**
- Focus on pushing knees outward
- Practice goblet squats for depth"""
        
        elif "report" in prompt.lower():
            content = """Weekly Progress Summary:

**Workouts Completed:** 4/5 planned sessions
**Total Volume:** 12,500 lbs lifted
**Average Intensity:** 75% of 1RM

**Key Achievements:**
- Squat PR: +10 lbs
- Consistency: 80%

**Areas for Focus:**
- Increase lower body frequency
- Improve sleep quality"""
        
        else:
            content = "Mock response for testing purposes. Enable real Bedrock for actual AI responses."
        
        return {
            "content": content,
            "model": "mock-model",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "stop_reason": "end_turn"
        }
    
    def _mock_agent_response(self, input_text: str) -> Dict[str, Any]:
        """Mock agent response."""
        return {
            "completion": f"Mock agent response to: {input_text}",
            "session_id": "mock-session",
            "trace": None
        }
    
    def _mock_kb_response(self, query: str) -> Dict[str, Any]:
        """Mock knowledge base response."""
        return {
            "results": [
                {
                    "content": f"Mock KB result for query: {query}",
                    "score": 0.95,
                    "location": {"type": "mock"}
                }
            ],
            "count": 1
        }


# Singleton instance
bedrock_client = BedrockClient()
