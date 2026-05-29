import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FleetLease"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://fleetlease:fleetlease_secret@localhost:5432/fleetlease"
    DATABASE_URL_SYNC: str = "postgresql://fleetlease:fleetlease_secret@localhost:5432/fleetlease"

    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "fleetlease"
    MINIO_ABOUT_BUCKET: str = "about-site"
    MINIO_SECURE: bool = False
    MINIO_EXTERNAL_ENDPOINT: str = "localhost:9000"

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    NBRB_BASE_URL: str = "https://api.nbrb.by"
    NBRB_REQUEST_TIMEOUT: float = 15.0

    VAT_RATE_PERCENT: float = 20.0

    # SMTP (fastapi-mail). Если MAIL_SERVER пуст — отправка почты недоступна (503 на forgot-password).
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "FleetLease"
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON value must be a list of origins")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        raise ValueError("Unsupported CORS_ORIGINS format")

    @property
    def minio_external_base_url(self) -> str:
        endpoint = self.MINIO_EXTERNAL_ENDPOINT.strip().rstrip("/")
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        scheme = "https" if self.MINIO_SECURE else "http"
        return f"{scheme}://{endpoint}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
