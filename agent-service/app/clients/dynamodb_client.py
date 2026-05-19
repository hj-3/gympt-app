import aioboto3
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class AsyncDynamoDBClient:
    """Async DynamoDB client for logging agent interactions."""

    def __init__(self):
        self.session = aioboto3.Session()
        self.table_name = settings.dynamodb_agent_interactions_table
        self.region = settings.aws_region
        self.endpoint_url = settings.dynamodb_endpoint_url

    async def log_interaction(
        self,
        user_id: str,
        interaction_type: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        model_id: str,
        tokens_used: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        Log an agent interaction to DynamoDB.

        Args:
            user_id: User identifier
            interaction_type: Type of interaction (workout_recommend, posture_feedback, report_generation)
            request_data: Request payload
            response_data: Response payload
            model_id: Bedrock model ID used
            tokens_used: Token usage metrics (input_tokens, output_tokens)

        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            item = {
                "user_id": user_id,
                "timestamp": timestamp,
                "interaction_type": interaction_type,
                "request_data": request_data,
                "response_data": response_data,
                "model_id": model_id,
                "tokens_used": tokens_used or {},
                "environment": settings.app_env
            }

            async with self.session.resource(
                "dynamodb",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)
                await table.put_item(Item=item)

            logger.info(
                f"Logged interaction: user={user_id}, type={interaction_type}, "
                f"timestamp={timestamp}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to log interaction to DynamoDB: {e}")
            # Don't raise - graceful degradation
            return False

    async def get_user_interactions(
        self,
        user_id: str,
        interaction_type: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """
        Retrieve user interactions from DynamoDB.

        Args:
            user_id: User identifier
            interaction_type: Optional filter by interaction type
            limit: Maximum number of items to retrieve

        Returns:
            List of interaction records
        """
        try:
            async with self.session.resource(
                "dynamodb",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)

                if interaction_type:
                    # Use GSI for querying by interaction_type
                    response = await table.query(
                        IndexName="interaction_type-timestamp-index",
                        KeyConditionExpression="interaction_type = :type",
                        FilterExpression="user_id = :uid",
                        ExpressionAttributeValues={
                            ":type": interaction_type,
                            ":uid": user_id
                        },
                        Limit=limit,
                        ScanIndexForward=False  # Most recent first
                    )
                else:
                    # Query by user_id partition key
                    response = await table.query(
                        KeyConditionExpression="user_id = :uid",
                        ExpressionAttributeValues={
                            ":uid": user_id
                        },
                        Limit=limit,
                        ScanIndexForward=False
                    )

                return response.get("Items", [])

        except Exception as e:
            logger.error(f"Failed to retrieve interactions from DynamoDB: {e}")
            return []


# Singleton instance
dynamodb_client = AsyncDynamoDBClient()
