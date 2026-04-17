"""Официальные курсы НБ РБ (api.nbrb.by) с кэшем в памяти процесса."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings

CACHE_TTL = timedelta(minutes=45)

_nbrb_cache: dict[str, Any] | None = None
_cache_valid_until: datetime | None = None


@dataclass(frozen=True)
class NbrbRateRow:
    code: str
    """Буквенный код ISO (USD, EUR)."""
    rate_byn_per_unit: float
    """Сколько BYN за 1 единицу иностранной валюты (с учётом Cur_Scale)."""
    scale: int
    official_rate: float
    date: date


def _normalize_rate_payload(data: Any) -> dict[str, Any]:
    if isinstance(data, list):
        if not data:
            raise ValueError("Пустой ответ курса НБ РБ")
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError("Неожиданный формат ответа НБ РБ")


def _parse_rate_row(raw: dict[str, Any]) -> NbrbRateRow:
    scale = int(raw.get("Cur_Scale") or 1)
    official = float(raw["Cur_OfficialRate"])
    abbrev = str(raw.get("Cur_Abbreviation") or "")
    date_str = raw.get("Date")
    if isinstance(date_str, str):
        d = date.fromisoformat(date_str[:10])
    else:
        d = date.today()
    per_unit = official / scale if scale else official
    return NbrbRateRow(
        code=abbrev,
        rate_byn_per_unit=per_unit,
        scale=scale,
        official_rate=official,
        date=d,
    )


async def _fetch_one_iso(client: httpx.AsyncClient, iso_code: str) -> NbrbRateRow:
    """Курс по буквенному коду ISO 4217 (parammode=2)."""
    url = f"{settings.NBRB_BASE_URL.rstrip('/')}/exrates/rates/{iso_code}"
    resp = await client.get(url, params={"periodicity": 0, "parammode": 2})
    resp.raise_for_status()
    return _parse_rate_row(_normalize_rate_payload(resp.json()))


async def fetch_nbrb_rates() -> tuple[NbrbRateRow, NbrbRateRow]:
    """Загружает курсы USD и EUR с НБ РБ."""
    timeout = httpx.Timeout(settings.NBRB_REQUEST_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
        usd_task = asyncio.create_task(_fetch_one_iso(client, "USD"))
        eur_task = asyncio.create_task(_fetch_one_iso(client, "EUR"))
        usd, eur = await asyncio.gather(usd_task, eur_task)
        return usd, eur


def _cache_stale() -> bool:
    if _nbrb_cache is None or _cache_valid_until is None:
        return True
    return datetime.utcnow() >= _cache_valid_until


async def get_exchange_rates_payload() -> dict[str, Any]:
    """
    Возвращает структуру для API: курсы BYN (база), USD, EUR.
    При ошибке сети отдаёт последний успешный кэш, если он есть.
    """
    global _nbrb_cache, _cache_valid_until

    if not _cache_stale() and _nbrb_cache is not None:
        return _nbrb_cache

    try:
        usd, eur = await fetch_nbrb_rates()
        rate_date = max(usd.date, eur.date)
        payload = {
            "rate_date": rate_date.isoformat(),
            "currencies": [
                {
                    "code": "BYN",
                    "flag": "🇧🇾",
                    "rate_byn_per_unit": 1.0,
                },
                {
                    "code": usd.code or "USD",
                    "flag": "🇺🇸",
                    "rate_byn_per_unit": round(usd.rate_byn_per_unit, 6),
                },
                {
                    "code": eur.code or "EUR",
                    "flag": "🇪🇺",
                    "rate_byn_per_unit": round(eur.rate_byn_per_unit, 6),
                },
            ],
        }
        _nbrb_cache = payload
        _cache_valid_until = datetime.utcnow() + CACHE_TTL
        return payload
    except Exception:
        if _nbrb_cache is not None:
            return _nbrb_cache
        raise
