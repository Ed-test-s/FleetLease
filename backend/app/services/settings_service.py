from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.app_settings import AppSettings

SETTINGS_ROW_ID = 1


async def ensure_app_settings_row(db: AsyncSession) -> AppSettings:
    result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ROW_ID))
    row = result.scalar_one_or_none()
    if row is None:
        row = AppSettings(id=SETTINGS_ROW_ID, vat_rate_percent=settings.VAT_RATE_PERCENT)
        db.add(row)
        await db.flush()
    return row


async def get_vat_rate_percent(db: AsyncSession) -> float:
    result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ROW_ID))
    row = result.scalar_one_or_none()
    if row is None:
        return settings.VAT_RATE_PERCENT
    return float(row.vat_rate_percent)
