from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import (
    BankAccount,
    Company,
    Entrepreneur,
    Individual,
    User,
    UserContact,
    UserRole,
    UserType,
)
from app.schemas.user import TokenResponse, UserOut, UserRegister, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.login == data.login))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Login already taken")

    if data.role == UserRole.LEASE_MANAGER and data.user_type != UserType.COMPANY:
        raise HTTPException(status_code=400, detail="Lease manager must be a company")

    user = User(
        login=data.login,
        password_hash=hash_password(data.password),
        role=data.role,
        user_type=data.user_type,
    )
    db.add(user)
    await db.flush()

    for c in data.contacts:
        db.add(UserContact(user_id=user.id, type=c.type, value=c.value, is_primary=c.is_primary))

    if data.user_type == UserType.INDIVIDUAL and data.individual:
        db.add(Individual(user_id=user.id, **data.individual.model_dump()))
    elif data.user_type == UserType.IE and data.entrepreneur:
        db.add(Entrepreneur(user_id=user.id, **data.entrepreneur.model_dump()))
    elif data.user_type == UserType.COMPANY and data.company:
        db.add(Company(user_id=user.id, **data.company.model_dump()))

    await db.flush()

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.contacts),
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
            selectinload(User.bank_accounts),
            selectinload(User.lease_terms),
        )
        .where(User.id == user.id)
    )
    return result.scalar_one()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Авторизация по логину, номеру телефона или email."""
    result = await db.execute(
        select(User)
        .outerjoin(UserContact)
        .where(
            or_(
                User.login == data.identifier,
                UserContact.value == data.identifier,
            )
        )
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)
