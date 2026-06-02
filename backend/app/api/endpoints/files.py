from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from minio.error import S3Error

from app.core.config import settings
from app.services.storage import storage_service

router = APIRouter(prefix="/files", tags=["files"])


def _validate_object_key(object_key: str) -> str:
    cleaned = object_key.strip().strip("/")
    if not cleaned:
        raise HTTPException(status_code=400, detail="Invalid file key")
    if "\\" in cleaned or any(part == ".." for part in cleaned.split("/")):
        raise HTTPException(status_code=400, detail="Invalid file key")
    return cleaned


@router.get("/{bucket}/{object_key:path}", status_code=302)
async def redirect_to_presigned_file(bucket: str, object_key: str):
    allowed_buckets = {settings.MINIO_BUCKET, settings.MINIO_ABOUT_BUCKET}
    if bucket not in allowed_buckets:
        raise HTTPException(status_code=400, detail="Bucket is not allowed")

    safe_key = _validate_object_key(object_key)
    try:
        storage_service.client.stat_object(bucket, safe_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="File not found") from None
        raise HTTPException(status_code=500, detail="Storage is unavailable") from None

    try:
        presigned_url = storage_service.get_presigned_get_url(
            bucket=bucket,
            object_key=safe_key,
        )
    except S3Error:
        raise HTTPException(status_code=500, detail="Storage is unavailable") from None

    return RedirectResponse(url=presigned_url, status_code=302)
