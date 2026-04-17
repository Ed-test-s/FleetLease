from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.settings import AppSettingsOut, AppSettingsPatch
from app.services import settings_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings", response_model=AppSettingsOut)
async def get_admin_settings(
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    row = await settings_service.ensure_app_settings_row(db)
    return AppSettingsOut(vat_rate_percent=row.vat_rate_percent)


@router.patch("/settings", response_model=AppSettingsOut)
async def patch_admin_settings(
    data: AppSettingsPatch,
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    row = await settings_service.ensure_app_settings_row(db)
    row.vat_rate_percent = data.vat_rate_percent
    await db.flush()
    return AppSettingsOut(vat_rate_percent=row.vat_rate_percent)
