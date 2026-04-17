from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AppSettings(Base):
    """Singleton-настройки приложения (строка id=1)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vat_rate_percent: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)
