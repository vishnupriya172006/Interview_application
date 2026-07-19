from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp
from sqlalchemy import text

from app.api import auth, interviews, monitoring, reports
from app.core.config import settings
from app.core.database import Base, engine
from app.sockets.handlers import sio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Verify PostgreSQL and ensure the current schema exists before serving."""
    import app.models  # Register every model with Base.metadata.

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    Base.metadata.create_all(bind=engine)
    logger.info("Database connection verified and schema is ready.")
    yield
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URLS + ["http://localhost:3000"],
    allow_origin_regex=r"http://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(interviews, prefix=f"{settings.API_V1_STR}/interviews", tags=["interviews"])
app.include_router(reports, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(monitoring, prefix=f"{settings.API_V1_STR}/monitoring", tags=["monitoring"])


@app.get("/", tags=["health"])
def read_root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
    }


# Keep Socket.IO isolated under its conventional endpoint while preserving a
# FastAPI object for dependency overrides, OpenAPI, and middleware.
app.mount("/socket.io", ASGIApp(sio, socketio_path=""))
