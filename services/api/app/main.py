from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings
from app.routers.health import router as health_router

settings = get_settings()
allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="TravelMate backend foundation for secure user auth, profile handling, verification, and compliance-ready APIs.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": exc.detail.get("error", {}).get("code", "AUTHENTICATION_REQUIRED"),
                    "message": exc.detail.get("error", {}).get("message", "Authentication required."),
                }
            },
        )

    error_payload = {
        "error": {
            "code": "HTTP_ERROR",
            "message": exc.detail if isinstance(exc.detail, str) else "Request failed.",
        }
    }
    if isinstance(exc.detail, dict):
        error_payload = exc.detail
    return JSONResponse(status_code=exc.status_code, content=error_payload)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to TravelMate API",
        "environment": settings.app_environment,
        "version": settings.api_version,
    }
