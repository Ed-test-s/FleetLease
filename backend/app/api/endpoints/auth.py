import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import (
    Company,
    ContactType,
    Entrepreneur,
    Individual,
    User,
    UserContact,
    UserRole,
    UserType,
)
from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    TokenResponse,
    UserOut,
    UserRegister,
)
from app.services.mail import is_mail_configured, send_temporary_password_email

logger = logging.getLogger(__name__)

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
    identifier = data.identifier.strip()
    contact_user_ids = select(UserContact.user_id).where(UserContact.value == identifier)
    result = await db.execute(
        select(User)
        .where(
            or_(
                User.login == identifier,
                User.id.in_(contact_user_ids),
            )
        )
        .limit(1)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)


_FORGOT_PASSWORD_MESSAGE = (
    "Если для этого адреса есть учётная запись, на указанный email отправлено письмо с временным паролем."
)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Восстановление доступа: временный пароль на email из контактов пользователя."""
    if not is_mail_configured():
        raise HTTPException(
            status_code=503,
            detail="Отправка почты не настроена на сервере. Обратитесь к администратору.",
        )

    email_norm = data.email.strip().lower()
    result = await db.execute(
        select(User)
        .join(UserContact, User.id == UserContact.user_id)
        .where(
            UserContact.type == ContactType.EMAIL,
            func.lower(UserContact.value) == email_norm,
            User.is_active.is_(True),
        )
        .limit(1)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return MessageResponse(message=_FORGOT_PASSWORD_MESSAGE)

    temp_password = secrets.token_urlsafe(16)
    user.password_hash = hash_password(temp_password)
    await db.flush()

    try:
        await send_temporary_password_email(data.email.strip(), temp_password)
    except Exception:
        logger.exception("forgot-password: не удалось отправить письмо через SMTP")
        raise HTTPException(
            status_code=503,
            detail="Не удалось отправить письмо. Попробуйте позже или обратитесь к администратору.",
        ) from None

    return MessageResponse(message=_FORGOT_PASSWORD_MESSAGE)
