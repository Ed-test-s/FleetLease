from pydantic import BaseModel


class VehicleBrandOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class VehicleModelOut(BaseModel):
    id: int
    brand_id: int
    name: str
    model_config = {"from_attributes": True}


class VehicleBrandWithModelsOut(BaseModel):
    id: int
    name: str
    models: list[VehicleModelOut] = []
    model_config = {"from_attributes": True}


class ColourOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class CityOut(BaseModel):
    id: int
    region_id: int
    name: str
    model_config = {"from_attributes": True}


class RegionOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class RegionWithCitiesOut(BaseModel):
    id: int
    name: str
    cities: list[CityOut] = []
    model_config = {"from_attributes": True}


class NameCreate(BaseModel):
    name: str


class ModelCreate(BaseModel):
    brand_id: int
    name: str


class CityCreate(BaseModel):
    region_id: int
    name: str
