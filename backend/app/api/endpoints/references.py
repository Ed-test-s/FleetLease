from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.reference import City, Colour, Region, VehicleBrand, VehicleModel
from app.models.user import User, UserRole
from app.schemas.reference import (
    CityCreate,
    CityOut,
    ColourOut,
    ModelCreate,
    NameCreate,
    RegionOut,
    RegionWithCitiesOut,
    VehicleBrandOut,
    VehicleBrandWithModelsOut,
    VehicleModelOut,
)

router = APIRouter(prefix="/references", tags=["references"])


# ── Brands ────────────────────────────────────────────────────────────
@router.get("/brands", response_model=list[VehicleBrandWithModelsOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VehicleBrand)
        .options(selectinload(VehicleBrand.models))
        .order_by(VehicleBrand.name)
    )
    return result.scalars().unique().all()


@router.post("/brands", response_model=VehicleBrandOut, status_code=201)
async def create_brand(
    data: NameCreate,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(VehicleBrand).where(VehicleBrand.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Brand already exists")
    brand = VehicleBrand(name=data.name)
    db.add(brand)
    await db.flush()
    return brand


@router.post("/models", response_model=VehicleModelOut, status_code=201)
async def create_model(
    data: ModelCreate,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    model = VehicleModel(brand_id=data.brand_id, name=data.name)
    db.add(model)
    await db.flush()
    return model


@router.delete("/brands/{brand_id}", status_code=204)
async def delete_brand(
    brand_id: int,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VehicleBrand).where(VehicleBrand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    await db.delete(brand)


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: int,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VehicleModel).where(VehicleModel.id == model_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(m)


# ── Colours ───────────────────────────────────────────────────────────
@router.get("/colours", response_model=list[ColourOut])
async def list_colours(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Colour).order_by(Colour.name))
    return result.scalars().all()


@router.post("/colours", response_model=ColourOut, status_code=201)
async def create_colour(
    data: NameCreate,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Colour).where(Colour.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Colour already exists")
    colour = Colour(name=data.name)
    db.add(colour)
    await db.flush()
    return colour


@router.delete("/colours/{colour_id}", status_code=204)
async def delete_colour(
    colour_id: int,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Colour).where(Colour.id == colour_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Colour not found")
    await db.delete(c)


# ── Regions & Cities ──────────────────────────────────────────────────
@router.get("/regions", response_model=list[RegionWithCitiesOut])
async def list_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Region).options(selectinload(Region.cities)).order_by(Region.name)
    )
    return result.scalars().unique().all()


@router.post("/regions", response_model=RegionOut, status_code=201)
async def create_region(
    data: NameCreate,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    region = Region(name=data.name)
    db.add(region)
    await db.flush()
    return region


@router.post("/cities", response_model=CityOut, status_code=201)
async def create_city(
    data: CityCreate,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    city = City(region_id=data.region_id, name=data.name)
    db.add(city)
    await db.flush()
    return city
