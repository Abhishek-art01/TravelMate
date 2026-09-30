from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "travelmate-api",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    return {
        "status": "ready",
        "checks": {
            "database": "not-run",
            "cache": "not-run",
            "auth": "not-run",
        },
    }
