from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_optional_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle, VehicleCondition, VehicleImage
from app.schemas.vehicle import VehicleCreate, VehicleListOut, VehicleOut, VehicleUpdate
from app.services.storage import storage_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/", response_model=list[VehicleListOut])
async def list_vehicles(
    search: str | None = None,
    brand: str | None = None,
    model: str | None = None,
    vehicle_type: str | None = None,
    condition: VehicleCondition | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    mileage_min: int | None = None,
    mileage_max: int | None = None,
    fuel_type: str | None = None,
    drive_type: str | None = None,
    transmission: str | None = None,
    location: str | None = None,
    colour: str | None = None,
    in_stock: bool | None = None,
    supplier_id: int | None = None,
    sort_by: str = Query("newest", regex="^(newest|oldest|price_asc|price_desc|mileage_asc|year_desc|year_asc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    q = select(Vehicle).options(selectinload(Vehicle.images)).where(Vehicle.is_visible.is_(True))

    if search:
        pattern = f"%{search}%"
        q = q.where(Vehicle.name.ilike(pattern) | Vehicle.brand.ilike(pattern) | Vehicle.model.ilike(pattern))
    if brand:
        q = q.where(Vehicle.brand.ilike(f"%{brand}%"))
    if model:
        q = q.where(Vehicle.model.ilike(f"%{model}%"))
    if vehicle_type:
        q = q.where(Vehicle.vehicle_type == vehicle_type)
    if condition:
        q = q.where(Vehicle.condition == condition)
    if price_min is not None:
        q = q.where(Vehicle.price >= price_min)
    if price_max is not None:
        q = q.where(Vehicle.price <= price_max)
    if year_min is not None:
        q = q.where(Vehicle.release_year >= year_min)
    if year_max is not None:
        q = q.where(Vehicle.release_year <= year_max)
    if mileage_min is not None:
        q = q.where(Vehicle.mileage >= mileage_min)
    if mileage_max is not None:
        q = q.where(Vehicle.mileage <= mileage_max)
    if fuel_type:
        q = q.where(Vehicle.fuel_type == fuel_type)
    if drive_type:
        q = q.where(Vehicle.drive_type == drive_type)
    if transmission:
        q = q.where(Vehicle.transmission.ilike(f"%{transmission}%"))
    if location:
        q = q.where(Vehicle.location.ilike(f"%{location}%"))
    if colour:
        q = q.where(Vehicle.colour.ilike(f"%{colour}%"))
    if in_stock:
        q = q.where(Vehicle.count > 0)
    if supplier_id:
        q = q.where(Vehicle.supplier_id == supplier_id)

    sort_map = {
        "newest": Vehicle.created_at.desc(),
        "oldest": Vehicle.created_at.asc(),
        "price_asc": Vehicle.price.asc(),
        "price_desc": Vehicle.price.desc(),
        "mileage_asc": Vehicle.mileage.asc(),
        "year_desc": Vehicle.release_year.desc(),
        "year_asc": Vehicle.release_year.asc(),
    }
    q = q.order_by(sort_map.get(sort_by, Vehicle.created_at.desc()))
    q = q.offset(skip).limit(limit)

    result = await db.execute(q)
    return result.scalars().unique().all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Vehicle).options(selectinload(Vehicle.images)).where(Vehicle.id == vehicle_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/", response_model=VehicleOut, status_code=201)
async def create_vehicle(
    data: VehicleCreate,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    vehicle = Vehicle(supplier_id=user.id, **data.model_dump())
    db.add(vehicle)
    await db.flush()
    result = await db.execute(
        select(Vehicle).options(selectinload(Vehicle.images)).where(Vehicle.id == vehicle.id)
    )
    return result.scalar_one()


@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).options(selectinload(Vehicle.images)).where(
            Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(vehicle, k, v)
    await db.flush()
    return vehicle


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(
    vehicle_id: int,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")
    await db.delete(vehicle)


@router.post("/{vehicle_id}/images", response_model=VehicleOut)
async def upload_vehicle_image(
    vehicle_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).options(selectinload(Vehicle.images)).where(
            Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")

    url = await storage_service.upload_file(file, folder="vehicles")
    db.add(VehicleImage(vehicle_id=vehicle.id, image_url=url))
    await db.flush()

    result = await db.execute(
        select(Vehicle).options(selectinload(Vehicle.images)).where(Vehicle.id == vehicle.id)
    )
    return result.scalar_one()


@router.delete("/{vehicle_id}/images/{image_id}", status_code=204)
async def delete_vehicle_image(
    vehicle_id: int,
    image_id: int,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VehicleImage).where(
            VehicleImage.id == image_id,
            VehicleImage.vehicle_id == vehicle_id,
        )
    )
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    v_result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id)
    )
    if not v_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(img)
