from pydantic import BaseModel, Field


class AppSettingsOut(BaseModel):
    vat_rate_percent: float


class AppSettingsPatch(BaseModel):
    vat_rate_percent: float = Field(ge=0.0, le=100.0)
