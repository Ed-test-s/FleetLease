from datetime import datetime

from pydantic import BaseModel

from app.schemas.vehicle import VehicleImageOut


class FavoriteOut(BaseModel):
    id: int
    vehicle_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteVehicleOut(BaseModel):
    id: int
    vehicle_id: int
    created_at: datetime
    vehicle_name: str
    vehicle_brand: str
    vehicle_model: str
    vehicle_price: float
    vehicle_condition: str
    vehicle_location: str | None = None
    vehicle_release_year: int | None = None
    vehicle_mileage: int | None = None
    vehicle_fuel_type: str | None = None
    vehicle_images: list[VehicleImageOut] = []

    model_config = {"from_attributes": True}
