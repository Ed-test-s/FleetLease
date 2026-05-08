from fastapi import APIRouter

from app.api.endpoints import about, admin_settings, auth, chats, exchange_rates, leasing, notifications, references, reviews, users, vehicles

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(exchange_rates.router)
api_router.include_router(admin_settings.router)
api_router.include_router(about.router)
api_router.include_router(users.router)
api_router.include_router(vehicles.router)
api_router.include_router(leasing.router)
api_router.include_router(chats.router)
api_router.include_router(notifications.router)
api_router.include_router(reviews.router)
api_router.include_router(references.router)
