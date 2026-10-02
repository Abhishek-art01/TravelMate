from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    blocks,
    destinations,
    discovery,
    me,
    media,
    preferences,
    privacy,
    profiles,
    reports,
    trips,
    users,
    verification,
)
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
api_router.include_router(verification.me_verification_router)
api_router.include_router(verification.admin_verification_router)
api_router.include_router(verification.webhook_verification_router)
api_router.include_router(destinations.router)
api_router.include_router(destinations.me_location_router)
api_router.include_router(destinations.admin_destinations_router)
api_router.include_router(trips.router)
api_router.include_router(trips.me_trips_router)
api_router.include_router(trips.admin_trips_router)
api_router.include_router(discovery.router)
api_router.include_router(blocks.router)
api_router.include_router(reports.router)
api_router.include_router(reports.admin_reports_router)
api_router.include_router(admin.router)

