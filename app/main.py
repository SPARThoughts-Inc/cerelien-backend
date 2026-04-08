from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import db
from app.api.error_handlers import register_exception_handlers
from app.api.routes.chat_routes import router as chat_router
from app.api.routes.health_routes import router as health_router
from app.api.routes.patient_routes import router as patient_router
from app.api.routes.sms_routes import router as sms_router
from app.api.routes.voice_routes import router as voice_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to DB
    await db.connect()
    yield
    # Shutdown: disconnect from DB
    await db.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cerelien Backend",
        version="0.1.0",
        description="Cerelien AI - Diabetes Consultation Platform",
        lifespan=lifespan,
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
    app.include_router(patient_router)
    app.include_router(chat_router)
    app.include_router(voice_router)
    app.include_router(sms_router)

    return app


app = create_app()
