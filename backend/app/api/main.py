"""
FastAPI application setup and middleware configuration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logger import setup_logging, get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application

    Returns:
        Configured FastAPI app instance
    """
    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level)

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="API for Energy Consumption Dashboard - Noida Campus",
        version=settings.app_version,
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request/response logging middleware
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"{request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Status code: {response.status_code}")
        return response

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": settings.app_name}

    # Include routers
    try:
        from app.routes import data, kpis, export, scheduler
        app.include_router(data.router)
        app.include_router(kpis.router)
        app.include_router(export.router)
        app.include_router(scheduler.router)
        logger.info("All routers loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load routers: {e}")
        raise

    return app


def get_app() -> FastAPI:
    """Get the FastAPI application instance"""
    return create_app()
