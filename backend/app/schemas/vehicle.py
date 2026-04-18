from datetime import datetime

from pydantic import BaseModel, Field

from app.models.vehicle import VehicleCondition


class VehicleImageOut(BaseModel):
    id: int
    image_url: str
    model_config = {"from_attributes": True}


class VehicleCreate(BaseModel):
    name: str
    brand: str
    model: str
    condition: VehicleCondition
    vehicle_type: str
    price: float = Field(..., gt=0)
    count: int = 1
    product_code: str | None = None
    release_year: int | None = None
    mileage: int | None = None
    vin: str | None = Field(None, max_length=17, min_length=17)
    colour: str | None = None
    region_id: int | None = None
    city_id: int | None = None
    location: str | None = None
    fuel_type: str | None = None
    engine_capacity: float | None = None
    hp: int | None = None
    transmission: str | None = None
    drive_type: str | None = None
    extras: str | None = None
    description: str | None = None
    is_visible: bool = True


class VehicleUpdate(VehicleCreate):
    name: str | None = None
    brand: str | None = None
    model: str | None = None
    condition: VehicleCondition | None = None
    vehicle_type: str | None = None
    price: float | None = None
    vin: str | None = None


class VehicleSellerOut(BaseModel):
    id: int
    display_name: str
    avatar_url: str | None = None


class VehicleOut(BaseModel):
    id: int
    supplier_id: int
    name: str
    brand: str
    model: str
    condition: VehicleCondition
    vehicle_type: str
    price: float
    count: int
    product_code: str | None = None
    release_year: int | None = None
    mileage: int | None = None
    vin: str | None = None
    colour: str | None = None
    region_id: int | None = None
    city_id: int | None = None
    location: str | None = None
    fuel_type: str | None = None
    engine_capacity: float | None = None
    hp: int | None = None
    transmission: str | None = None
    drive_type: str | None = None
    extras: str | None = None
    description: str | None = None
    is_visible: bool
    created_at: datetime
    images: list[VehicleImageOut] = []
    seller: VehicleSellerOut | None = None

    model_config = {"from_attributes": True}


class VehicleListOut(BaseModel):
    id: int
    supplier_id: int
    name: str
    brand: str
    model: str
    condition: VehicleCondition
    vehicle_type: str
    price: float
    count: int
    release_year: int | None = None
    mileage: int | None = None
    colour: str | None = None
    region_id: int | None = None
    city_id: int | None = None
    location: str | None = None
    fuel_type: str | None = None
    engine_capacity: float | None = None
    hp: int | None = None
    transmission: str | None = None
    drive_type: str | None = None
    is_visible: bool
    created_at: datetime
    images: list[VehicleImageOut] = []

    model_config = {"from_attributes": True}
