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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
