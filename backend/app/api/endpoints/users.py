from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.review import Review
from app.models.user import (
    BankAccount,
    Company,
    Entrepreneur,
    Individual,
    LeaseTerm,
    User,
    UserContact,
    UserRole,
    UserType,
)
from app.schemas.user import (
    BankAccountCreate,
    BankAccountOut,
    ContactCreate,
    ContactOut,
    LeaseTermCreate,
    LeaseTermOut,
    UserOut,
    UserPublicOut,
    UserUpdate,
)
from app.services.storage import storage_service

router = APIRouter(prefix="/users", tags=["users"])


async def _enrich_user_rating(db: AsyncSession, user_id: int) -> tuple[float | None, int]:
    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.target_id == user_id)
    )
    row = result.one()
    avg_rating = round(float(row[0]), 2) if row[0] else None
    return avg_rating, row[1]


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rating, count = await _enrich_user_rating(db, user.id)
    out = UserOut.model_validate(user)
    out.rating = rating
    out.reviews_count = count
    return out


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.description is not None:
        user.description = data.description
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    await db.flush()
    rating, count = await _enrich_user_rating(db, user.id)
    out = UserOut.model_validate(user)
    out.rating = rating
    out.reviews_count = count
    return out


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = await storage_service.upload_file(file, folder="avatars")
    user.avatar_url = url
    await db.flush()
    rating, count = await _enrich_user_rating(db, user.id)
    out = UserOut.model_validate(user)
    out.rating = rating
    out.reviews_count = count
    return out


@router.get("/{user_id}", response_model=UserPublicOut)
async def get_user_public(user_id: int, db: AsyncSession = Depends(get_db)):
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
        .where(User.id == user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rating, count = await _enrich_user_rating(db, user.id)
    out = UserPublicOut.model_validate(user)
    out.rating = rating
    out.reviews_count = count
    return out


@router.get("/", response_model=list[UserPublicOut])
async def list_users(
    role: UserRole | None = None,
    user_type: UserType | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(User)
        .options(
            selectinload(User.contacts),
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
            selectinload(User.lease_terms),
        )
        .where(User.is_active.is_(True))
    )
    if role:
        q = q.where(User.role == role)
    if user_type:
        q = q.where(User.user_type == user_type)
    if search:
        pattern = f"%{search}%"
        q = q.outerjoin(Individual).outerjoin(Entrepreneur).outerjoin(Company)
        q = q.where(
            User.login.ilike(pattern)
            | Individual.full_name.ilike(pattern)
            | Entrepreneur.full_name.ilike(pattern)
            | Company.company_name.ilike(pattern)
        )
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    users = result.scalars().unique().all()

    out_list = []
    for u in users:
        rating, count = await _enrich_user_rating(db, u.id)
        out = UserPublicOut.model_validate(u)
        out.rating = rating
        out.reviews_count = count
        out_list.append(out)
    return out_list


# ── Contacts ──────────────────────────────────────────────────────────
@router.post("/me/contacts", response_model=ContactOut)
async def add_contact(
    data: ContactCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = UserContact(user_id=user.id, **data.model_dump())
    db.add(contact)
    await db.flush()
    return contact


@router.delete("/me/contacts/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserContact).where(UserContact.id == contact_id, UserContact.user_id == user.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)


# ── Bank accounts ─────────────────────────────────────────────────────
@router.post("/me/bank-accounts", response_model=BankAccountOut)
async def add_bank_account(
    data: BankAccountCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ba = BankAccount(user_id=user.id, **data.model_dump())
    db.add(ba)
    await db.flush()
    return ba


@router.delete("/me/bank-accounts/{account_id}", status_code=204)
async def delete_bank_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BankAccount).where(BankAccount.id == account_id, BankAccount.user_id == user.id)
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Bank account not found")
    await db.delete(acc)


# ── Lease Terms (for lessors) ─────────────────────────────────────────
@router.put("/me/lease-terms", response_model=LeaseTermOut)
async def upsert_lease_terms(
    data: LeaseTermCreate,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LeaseTerm).where(LeaseTerm.user_id == user.id))
    lt = result.scalar_one_or_none()
    if lt:
        for k, v in data.model_dump().items():
            setattr(lt, k, v)
    else:
        lt = LeaseTerm(user_id=user.id, **data.model_dump())
        db.add(lt)
    await db.flush()
    return lt


# ── Admin: manage users ──────────────────────────────────────────────
@router.patch("/{user_id}/toggle-active", response_model=UserPublicOut)
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.contacts),
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
            selectinload(User.lease_terms),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    await db.flush()
    return UserPublicOut.model_validate(user)


@router.patch("/{user_id}/role", response_model=UserPublicOut)
async def change_user_role(
    user_id: int,
    role: UserRole,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.contacts),
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
            selectinload(User.lease_terms),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    await db.flush()
    return UserPublicOut.model_validate(user)
