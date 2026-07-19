from contextlib import asynccontextmanager
import logging

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from socketio import ASGIApp
from sqlalchemy import text

from app.api import auth, interviews, monitoring, reports
from app.core.config import settings
from app.core.database import Base, engine
from app.sockets.handlers import sio

logger = logging.getLogger(__name__)
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend-dist"


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


@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
    }


# Keep Socket.IO isolated under its conventional endpoint while preserving a
# FastAPI object for dependency overrides, OpenAPI, and middleware.
app.mount("/socket.io", ASGIApp(sio, socketio_path=""))

# The production Docker image includes the built Vite client. Serving it from
# FastAPI gives the browser one public Railway origin for the app, REST API,
# and Socket.IO signalling server.
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str):
        requested_file = (FRONTEND_DIST / path).resolve()
        if requested_file.is_relative_to(FRONTEND_DIST) and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def local_root():
        return health_check()
