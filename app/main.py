from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_exception_handlers
from app.api.routes.health_routes import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cerelien Backend",
        version="0.1.0",
        description="Cerelien AI - Diabetes Consultation Platform",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(health_router, tags=["health"])

    return app


app = create_app()
