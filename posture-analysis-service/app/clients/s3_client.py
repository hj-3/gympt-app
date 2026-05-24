"""Async S3 client for storing analysis results."""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import aioboto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class AsyncS3Client:
    """Async S3 client for uploading posture analysis results."""

    def __init__(self):
        """Initialize S3 client."""
        self.bucket_name = settings.s3_media_bucket
        self.prefix = settings.s3_posture_results_prefix
        self.session = aioboto3.Session()

        logger.info(f"AsyncS3Client initialized with bucket: {self.bucket_name}")

    async def upload_analysis_result(
        self,
        user_id: str,
        session_id: str,
        analysis_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Upload analysis result to S3.

        Args:
            user_id: User identifier
            session_id: Session identifier
            analysis_data: Complete analysis data to upload

        Returns:
            S3 key of uploaded object, or None if failed
        """
        try:
            # Generate S3 key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{self.prefix}/{user_id}/{session_id}/{timestamp}_results.json"

            # Serialize data to JSON
            json_data = json.dumps(analysis_data, indent=2, default=str)

            # Upload to S3
            async with self.session.client(
                "s3",
                region_name=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=json_data.encode("utf-8"),
                    ContentType="application/json",
                    Metadata={
                        "user_id": user_id,
                        "session_id": session_id,
                        "uploaded_at": datetime.utcnow().isoformat(),
                    }
                )

            logger.info(f"Uploaded analysis result to s3://{self.bucket_name}/{s3_key}")
            return s3_key

        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading analysis result: {e}")
            return None

    async def upload_frame_snapshot(
        self,
        user_id: str,
        session_id: str,
        frame_data: bytes,
        frame_number: int
    ) -> Optional[str]:
        """
        Upload a frame snapshot to S3.

        Args:
            user_id: User identifier
            session_id: Session identifier
            frame_data: Frame image data (JPEG bytes)
            frame_number: Frame sequence number

        Returns:
            S3 key of uploaded frame
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{self.prefix}/{user_id}/{session_id}/frames/frame_{frame_number}_{timestamp}.jpg"

            async with self.session.client(
                "s3",
                region_name=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=frame_data,
                    ContentType="image/jpeg",
                    Metadata={
                        "user_id": user_id,
                        "session_id": session_id,
                        "frame_number": str(frame_number),
                    }
                )

            logger.debug(f"Uploaded frame snapshot to s3://{self.bucket_name}/{s3_key}")
            return s3_key

        except Exception as e:
            logger.error(f"Error uploading frame snapshot: {e}")
            return None

    async def get_analysis_result(
        self,
        s3_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis result from S3.

        Args:
            s3_key: S3 key of the analysis result

        Returns:
            Analysis data dictionary
        """
        try:
            async with self.session.client(
                "s3",
                region_name=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
            ) as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )

                # Read and parse JSON
                data = await response["Body"].read()
                analysis_data = json.loads(data.decode("utf-8"))

                return analysis_data

        except ClientError as e:
            logger.error(f"S3 get object error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving analysis result: {e}")
            return None

    async def list_session_results(
        self,
        user_id: str,
        session_id: str
    ) -> List[str]:
        """
        List all result files for a session.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            List of S3 keys
        """
        try:
            prefix = f"{self.prefix}/{user_id}/{session_id}/"

            async with self.session.client(
                "s3",
                region_name=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
            ) as s3:
                response = await s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )

                return [obj["Key"] for obj in response.get("Contents", [])]

        except Exception as e:
            logger.error(f"Error listing session results: {e}")
            return []
