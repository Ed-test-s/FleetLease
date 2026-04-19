"""Проверка полноты банковских реквизитов для участия в сделках."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import BankAccount


def bank_account_row_is_complete(ba: BankAccount) -> bool:
    def nz(x: object) -> bool:
        return x is not None and str(x).strip() != ""

    if not nz(ba.iban):
        return False
    if not nz(ba.bank_name):
        return False
    if not nz(ba.bank_address):
        return False
    if not (nz(ba.bic) or nz(ba.swift)):
        return False
    return True


async def user_has_usable_bank_requisites(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(select(BankAccount).where(BankAccount.user_id == user_id))
    rows = result.scalars().all()
    return any(bank_account_row_is_complete(r) for r in rows)


async def ensure_user_has_bank_requisites(
    db: AsyncSession,
    user_id: int,
    detail: str = "Добавьте в профиль хотя бы один банковский счёт с полными реквизитами (IBAN, название и адрес банка, BIC или SWIFT).",
) -> None:
    if not await user_has_usable_bank_requisites(db, user_id):
        raise HTTPException(status_code=400, detail=detail)
