import json
import re
import uuid
from datetime import timedelta
from io import BytesIO
from urllib.parse import quote, urlparse

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
        self._presign_client: Minio | None = None
        self._presign_client_endpoint: str | None = None
        self._presign_client_secure: bool | None = None
        self._policy_set = False
        self._about_bucket_ready = False

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

    def _ensure_about_bucket(self) -> None:
        if self._about_bucket_ready:
            return
        bucket = settings.MINIO_ABOUT_BUCKET
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
        try:
            self.client.set_bucket_policy(bucket, _public_read_policy(bucket))
        except S3Error:
            pass
        self._about_bucket_ready = True

    @staticmethod
    def _external_presign_target() -> tuple[str, bool]:
        external = settings.MINIO_EXTERNAL_ENDPOINT.strip().rstrip("/")
        if external.startswith("http://") or external.startswith("https://"):
            parsed = urlparse(external)
            endpoint = parsed.netloc or parsed.path
            secure = parsed.scheme == "https"
            return endpoint, secure
        return external, settings.MINIO_SECURE

    def _client_for_presign(self) -> Minio:
        endpoint, secure = self._external_presign_target()
        if (
            self._presign_client is None
            or self._presign_client_endpoint != endpoint
            or self._presign_client_secure != secure
        ):
            self._presign_client = Minio(
                endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=secure,
                region="us-east-1",
            )
            self._presign_client_endpoint = endpoint
            self._presign_client_secure = secure
        return self._presign_client

    def _object_key_from_public_url(self, url: str | None) -> str | None:
        return self.extract_object_key(url, bucket=settings.MINIO_BUCKET)

    def remove_object_by_url(self, url: str | None) -> None:
        key = self._object_key_from_public_url(url)
        if not key:
            return
        try:
            self.client.remove_object(settings.MINIO_BUCKET, key)
        except S3Error:
            pass

    def _object_key_from_about_public_url(self, url: str | None) -> str | None:
        return self.extract_object_key(url, bucket=settings.MINIO_ABOUT_BUCKET)

    def remove_about_object_by_url(self, url: str | None) -> None:
        key = self._object_key_from_about_public_url(url)
        if not key:
            return
        try:
            self.client.remove_object(settings.MINIO_ABOUT_BUCKET, key)
        except S3Error:
            pass

    @staticmethod
    def _clean_object_key(object_key: str | None) -> str | None:
        if not object_key:
            return None
        cleaned = object_key.strip().lstrip("/")
        return cleaned or None

    def extract_object_key(self, value: str | None, *, bucket: str) -> str | None:
        if not value:
            return None
        raw = value.strip()
        if not raw:
            return None

        if "://" not in raw:
            if raw.startswith("/"):
                path = raw.strip("/")
            else:
                path = raw
                if path.startswith(f"{bucket}/"):
                    return self._clean_object_key(path[len(bucket) + 1 :])
                return self._clean_object_key(path)
        else:
            parsed = urlparse(raw)
            path = parsed.path.strip("/")

        prefix = f"{bucket}/"
        if path.startswith(prefix):
            return self._clean_object_key(path[len(prefix) :])

        api_prefix = settings.API_V1_PREFIX.strip("/")
        files_prefix = f"{api_prefix}/files/{bucket}/"
        if path.startswith(files_prefix):
            return self._clean_object_key(path[len(files_prefix) :])

        return None

    def to_media_api_url(self, value: str | None, *, bucket: str) -> str | None:
        if not value:
            return None
        key = self.extract_object_key(value, bucket=bucket)
        if not key:
            return value
        encoded_key = quote(key, safe="/")
        return f"{settings.API_V1_PREFIX}/files/{bucket}/{encoded_key}"

    def get_presigned_get_url(
        self,
        *,
        bucket: str,
        object_key: str,
        expires_seconds: int = 600,
    ) -> str:
        return self._client_for_presign().presigned_get_object(
            bucket,
            object_key,
            expires=timedelta(seconds=expires_seconds),
        )

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
        return f"{settings.minio_external_base_url}/{settings.MINIO_BUCKET}/{object_name}"

    async def upload_about_file(self, file: UploadFile, folder: str = "images") -> str:
        self._ensure_about_bucket()
        ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
        ext = re.sub(r"[^a-zA-Z0-9]", "", ext) or "bin"
        object_name = f"{folder}/{uuid.uuid4().hex}.{ext}"

        data = await file.read()
        self.client.put_object(
            settings.MINIO_ABOUT_BUCKET,
            object_name,
            BytesIO(data),
            length=len(data),
            content_type=file.content_type or "application/octet-stream",
        )
        return f"{settings.minio_external_base_url}/{settings.MINIO_ABOUT_BUCKET}/{object_name}"


storage_service = StorageService()
