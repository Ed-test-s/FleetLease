from fastapi import APIRouter

from app.api.endpoints import auth, chats, leasing, notifications, references, reviews, users, vehicles

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(vehicles.router)
api_router.include_router(leasing.router)
api_router.include_router(chats.router)
api_router.include_router(notifications.router)
api_router.include_router(reviews.router)
api_router.include_router(references.router)
