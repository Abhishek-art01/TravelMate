from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.health import router as health_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="TravelMate backend foundation with health endpoints, auth hooks, and extensible service boundaries.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


@app.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to TravelMate API",
        "environment": settings.app_environment,
        "version": settings.api_version,
    }
