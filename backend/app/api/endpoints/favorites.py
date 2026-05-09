from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_role
from app.models.favorite import Favorite
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.schemas.favorite import FavoriteOut, FavoriteVehicleOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/ids", response_model=list[int])
async def get_favorite_ids(
    user: User = Depends(require_role(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite.vehicle_id).where(Favorite.user_id == user.id)
    )
    return list(result.scalars().all())


@router.get("/", response_model=list[FavoriteVehicleOut])
async def list_favorites(
    user: User = Depends(require_role(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite)
        .options(selectinload(Favorite.vehicle).selectinload(Vehicle.images))
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    )
    favorites = result.scalars().all()
    return [
        FavoriteVehicleOut(
            id=f.id,
            vehicle_id=f.vehicle_id,
            created_at=f.created_at,
            vehicle_name=f.vehicle.name,
            vehicle_brand=f.vehicle.brand,
            vehicle_model=f.vehicle.model,
            vehicle_price=f.vehicle.price,
            vehicle_condition=f.vehicle.condition.value,
            vehicle_location=f.vehicle.location,
            vehicle_release_year=f.vehicle.release_year,
            vehicle_mileage=f.vehicle.mileage,
            vehicle_fuel_type=f.vehicle.fuel_type,
            vehicle_images=[{"id": img.id, "image_url": img.image_url} for img in f.vehicle.images],
        )
        for f in favorites
    ]


@router.post("/{vehicle_id}", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    vehicle_id: int,
    user: User = Depends(require_role(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    existing = await db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.vehicle_id == vehicle_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already in favorites")

    fav = Favorite(user_id=user.id, vehicle_id=vehicle_id)
    db.add(fav)
    await db.flush()
    await db.refresh(fav)
    return fav


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    vehicle_id: int,
    user: User = Depends(require_role(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(Favorite).where(Favorite.user_id == user.id, Favorite.vehicle_id == vehicle_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
