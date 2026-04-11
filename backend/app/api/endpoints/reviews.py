from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewOut, status_code=201)
async def create_review(
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.target_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    existing = await db.execute(
        select(Review).where(Review.author_id == user.id, Review.target_id == data.target_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already reviewed this user")

    review = Review(author_id=user.id, **data.model_dump())
    db.add(review)

    db.add(Notification(
        user_id=data.target_id,
        title="Новый отзыв",
        text=f"Вам оставили отзыв с оценкой {data.rating}/5.",
    ))

    await db.flush()
    return review


@router.get("/user/{user_id}", response_model=list[ReviewOut])
async def get_user_reviews(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .where(Review.target_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
