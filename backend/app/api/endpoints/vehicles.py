from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_optional_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole, UserType
from app.models.vehicle import Vehicle, VehicleCondition, VehicleImage
from app.schemas.vehicle import VehicleCreate, VehicleListOut, VehicleOut, VehicleSellerOut, VehicleUpdate
from app.services.storage import storage_service
from app.services.user_display import user_display_name

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _validate_visibility_with_count(
    *, count: int, is_visible: bool, explicit_visibility: bool
) -> bool:
    if count < 0:
        raise HTTPException(status_code=400, detail="Количество не может быть отрицательным")
    if count <= 0:
        if explicit_visibility and is_visible:
            raise HTTPException(
                status_code=400,
                detail="Нельзя включить объявление при нулевом количестве техники",
            )
        return False
    return is_visible


def _vehicle_detail_load():
    return (
        selectinload(Vehicle.images),
        selectinload(Vehicle.supplier).options(
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
        ),
    )


def vehicle_to_out(vehicle: Vehicle) -> VehicleOut:
    out = VehicleOut.model_validate(vehicle)
    sup = vehicle.supplier
    if sup is None:
        return out
    display_name = user_display_name(sup) or sup.login
    return out.model_copy(
        update={
            "seller": VehicleSellerOut(
                id=sup.id,
                display_name=display_name,
                avatar_url=sup.avatar_url,
            )
        }
    )


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
    colour: str | None = None,
    region_id: int | None = None,
    city_id: int | None = None,
    in_stock: bool | None = None,
    supplier_id: int | None = None,
    supplier_type: str | None = Query(None, description="Comma-separated: individual,ie,company"),
    engine_capacity_min: float | None = None,
    engine_capacity_max: float | None = None,
    hp_min: int | None = None,
    hp_max: int | None = None,
    sort_by: str = Query("newest", pattern="^(newest|oldest|price_asc|price_desc|mileage_asc|year_desc|year_asc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    q = select(Vehicle).options(selectinload(Vehicle.images))
    own_catalog = (
        supplier_id is not None
        and user is not None
        and user.id == supplier_id
    )
    if not own_catalog:
        q = q.where(Vehicle.is_visible.is_(True))

    if search:
        pattern = f"%{search}%"
        q = q.where(Vehicle.name.ilike(pattern) | Vehicle.brand.ilike(pattern) | Vehicle.model.ilike(pattern))
    if brand:
        q = q.where(Vehicle.brand == brand)
    if model:
        q = q.where(Vehicle.model == model)
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
        q = q.where(Vehicle.transmission == transmission)
    if colour:
        q = q.where(Vehicle.colour == colour)
    if region_id is not None:
        q = q.where(Vehicle.region_id == region_id)
    if city_id is not None:
        q = q.where(Vehicle.city_id == city_id)
    if in_stock:
        q = q.where(Vehicle.count > 0)
    if supplier_id:
        q = q.where(Vehicle.supplier_id == supplier_id)
    if supplier_type:
        types = [t.strip() for t in supplier_type.split(",") if t.strip()]
        valid = [UserType(t) for t in types if t in UserType.__members__.values()]
        if valid:
            q = q.join(User, Vehicle.supplier_id == User.id).where(User.user_type.in_(valid))
    if engine_capacity_min is not None:
        q = q.where(Vehicle.engine_capacity >= engine_capacity_min)
    if engine_capacity_max is not None:
        q = q.where(Vehicle.engine_capacity <= engine_capacity_max)
    if hp_min is not None:
        q = q.where(Vehicle.hp >= hp_min)
    if hp_max is not None:
        q = q.where(Vehicle.hp <= hp_max)

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
async def get_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    result = await db.execute(
        select(Vehicle).options(*_vehicle_detail_load()).where(Vehicle.id == vehicle_id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if not vehicle.is_visible and (user is None or user.id != vehicle.supplier_id):
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle_to_out(vehicle)


@router.post("/", response_model=VehicleOut, status_code=201)
async def create_vehicle(
    data: VehicleCreate,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    visible = _validate_visibility_with_count(
        count=data.count,
        is_visible=data.is_visible,
        explicit_visibility=True,
    )
    payload = data.model_dump()
    payload["is_visible"] = visible
    vehicle = Vehicle(supplier_id=user.id, **payload)
    db.add(vehicle)
    await db.flush()
    result = await db.execute(
        select(Vehicle).options(*_vehicle_detail_load()).where(Vehicle.id == vehicle.id)
    )
    return vehicle_to_out(result.scalar_one())


@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).options(*_vehicle_detail_load()).where(
            Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")
    update_data = data.model_dump(exclude_unset=True)
    final_count = update_data.get("count", vehicle.count)
    final_visible = update_data.get("is_visible", vehicle.is_visible)
    explicit_visibility = "is_visible" in update_data
    update_data["is_visible"] = _validate_visibility_with_count(
        count=final_count,
        is_visible=final_visible,
        explicit_visibility=explicit_visibility,
    )
    for k, v in update_data.items():
        setattr(vehicle, k, v)
    await db.flush()
    return vehicle_to_out(vehicle)


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(
    vehicle_id: int,
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle)
        .options(selectinload(Vehicle.images))
        .where(Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")
    for img in vehicle.images:
        storage_service.remove_object_by_url(img.image_url)
    await db.delete(vehicle)


@router.post("/{vehicle_id}/images", response_model=VehicleOut)
async def upload_vehicle_image(
    vehicle_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.SUPPLIER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).options(*_vehicle_detail_load()).where(
            Vehicle.id == vehicle_id, Vehicle.supplier_id == user.id
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")

    url = await storage_service.upload_file(file, folder=f"vehicles/{vehicle_id}")
    db.add(VehicleImage(vehicle_id=vehicle.id, image_url=url))
    await db.flush()

    result = await db.execute(
        select(Vehicle).options(*_vehicle_detail_load()).where(Vehicle.id == vehicle.id)
    )
    return vehicle_to_out(result.scalar_one())


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

    storage_service.remove_object_by_url(img.image_url)
    await db.delete(img)
