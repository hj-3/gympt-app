"""
S3 service for report storage
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from io import BytesIO
from ..config.settings import settings


class S3Service:
    """Service for S3 operations"""

    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket_name = settings.S3_BUCKET_REPORTS

    def upload_report(
        self,
        file_buffer: BytesIO,
        s3_key: str,
    ) -> bool:
        """
        Upload report to S3

        Args:
            file_buffer: PDF file buffer
            s3_key: S3 object key

        Returns:
            True if successful
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_buffer.getvalue(),
                ContentType='application/pdf',
                ServerSideEncryption='AES256',
            )
            return True

        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return False

    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate presigned URL for report download

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL or None
        """
        if expiration is None:
            expiration = settings.S3_PRESIGNED_URL_EXPIRY

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                },
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def delete_report(self, s3_key: str) -> bool:
        """
        Delete report from S3

        Args:
            s3_key: S3 object key

        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True

        except ClientError as e:
            print(f"Error deleting from S3: {e}")
            return False

    def check_report_exists(self, s3_key: str) -> bool:
        """
        Check if report exists in S3

        Args:
            s3_key: S3 object key

        Returns:
            True if exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True

        except ClientError:
            return False
