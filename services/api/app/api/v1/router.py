from fastapi import APIRouter

from app.api.v1 import admin, auth, me, media, preferences, privacy, profiles, users, verification
from app.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(media.router)
api_router.include_router(users.router)
api_router.include_router(profiles.router)
api_router.include_router(preferences.router)
api_router.include_router(privacy.router)
api_router.include_router(verification.router)
api_router.include_router(admin.router)
