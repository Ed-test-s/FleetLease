from pydantic import BaseModel, Field


class CurrencyRateOut(BaseModel):
    code: str
    flag: str = Field(description="Эмодзи флага для UI")
    rate_byn_per_unit: float = Field(description="BYN за 1 единицу валюты (для BYN = 1)")


class ExchangeRatesOut(BaseModel):
    rate_date: str
    currencies: list[CurrencyRateOut]
