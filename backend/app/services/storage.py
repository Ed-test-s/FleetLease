import json
import re
import uuid
from io import BytesIO
from urllib.parse import urlparse

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


def _public_read_policy(bucket: str) -> str:
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
    )


class StorageService:
    def __init__(self):
        self._client: Minio | None = None
        self._policy_set = False

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            if not self._client.bucket_exists(settings.MINIO_BUCKET):
                self._client.make_bucket(settings.MINIO_BUCKET)
            if not self._policy_set:
                try:
                    self._client.set_bucket_policy(
                        settings.MINIO_BUCKET,
                        _public_read_policy(settings.MINIO_BUCKET),
                    )
                except S3Error:
                    pass
                self._policy_set = True
        return self._client

    def _object_key_from_public_url(self, url: str | None) -> str | None:
        if not url:
            return None
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        prefix = f"{settings.MINIO_BUCKET}/"
        if path.startswith(prefix):
            return path[len(prefix) :]
        if "/" in path:
            parts = path.split("/", 1)
            if parts[0] == settings.MINIO_BUCKET:
                return parts[1]
        return None

    def remove_object_by_url(self, url: str | None) -> None:
        key = self._object_key_from_public_url(url)
        if not key:
            return
        try:
            self.client.remove_object(settings.MINIO_BUCKET, key)
        except S3Error:
            pass

    async def upload_file(self, file: UploadFile, folder: str = "uploads") -> str:
        ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
        ext = re.sub(r"[^a-zA-Z0-9]", "", ext) or "bin"
        object_name = f"{folder}/{uuid.uuid4().hex}.{ext}"

        data = await file.read()
        self.client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            BytesIO(data),
            length=len(data),
            content_type=file.content_type or "application/octet-stream",
        )
        return f"http://{settings.MINIO_EXTERNAL_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"


storage_service = StorageService()
