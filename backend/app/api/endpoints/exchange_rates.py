from fastapi import APIRouter, HTTPException

from app.schemas.exchange_rates import CurrencyRateOut, ExchangeRatesOut
from app.services import nbrb_rates as nbrb_rates_svc

router = APIRouter(tags=["exchange-rates"])


@router.get("/exchange-rates", response_model=ExchangeRatesOut)
async def get_exchange_rates():
    """Официальные курсы НБ РБ: BYN (база), USD, EUR."""
    try:
        raw = await nbrb_rates_svc.get_exchange_rates_payload()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Не удалось получить курсы НБ РБ: {e!s}") from e

    currencies = [CurrencyRateOut(**c) for c in raw["currencies"]]
    return ExchangeRatesOut(rate_date=raw["rate_date"], currencies=currencies)
