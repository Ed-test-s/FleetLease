from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.about import AboutImageUploadOut, AboutPageContent
from app.services import about_service
from app.services.storage import storage_service

router = APIRouter(tags=["about"])


@router.get("/site/about", response_model=AboutPageContent)
async def get_about_public(db: AsyncSession = Depends(get_db)):
    return await about_service.get_about_content(db)


@router.get("/admin/about", response_model=AboutPageContent)
async def get_about_admin(
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await about_service.get_about_content(db)


@router.patch("/admin/about", response_model=AboutPageContent)
async def patch_about_admin(
    data: AboutPageContent,
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await about_service.save_about_content(db, data)


@router.post("/admin/about/upload-image", response_model=AboutImageUploadOut)
async def upload_about_image(
    file: UploadFile = File(...),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    url = await storage_service.upload_about_file(file, folder="about")
    return AboutImageUploadOut(url=url)
