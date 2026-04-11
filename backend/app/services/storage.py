import uuid
from io import BytesIO

from fastapi import UploadFile
from minio import Minio

from app.core.config import settings


class StorageService:
    def __init__(self):
        self._client: Minio | None = None

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
        return self._client

    async def upload_file(self, file: UploadFile, folder: str = "uploads") -> str:
        ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
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
