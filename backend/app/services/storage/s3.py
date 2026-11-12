import os
import boto3
from botocore.exceptions import ClientError
from app.config import settings
from app.services.storage.base import StorageService

class S3StorageService(StorageService):
    """AWS S3 / S3-compatible cloud storage implementation."""

    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        kwargs = {}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_REGION:
            kwargs["region_name"] = settings.AWS_REGION
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self.s3_client = boto3.client("s3", **kwargs)

    def _get_key(self, category: str, filename: str) -> str:
        return f"{category}/{filename}"

    def save_file(self, category: str, filename: str, content: bytes) -> str:
        key = self._get_key(category, filename)
        content_type = "model/gltf-binary" if filename.endswith(".glb") else "application/octet-stream"
        if filename.endswith(".png"):
            content_type = "image/png"
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type
        )
        return f"s3://{self.bucket}/{key}"

    def get_file_path(self, category: str, filename: str) -> str:
        # In cloud S3, returns the URI identifier
        return f"s3://{self.bucket}/{self._get_key(category, filename)}"

    def get_file_bytes(self, category: str, filename: str) -> bytes:
        key = self._get_key(category, filename)
        resp = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read()

    def delete_file(self, category: str, filename: str) -> bool:
        key = self._get_key(category, filename)
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def exists(self, category: str, filename: str) -> bool:
        key = self._get_key(category, filename)
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_download_url(self, category: str, filename: str, expires_in: int = 3600) -> str:
        key = self._get_key(category, filename)
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in
        )

