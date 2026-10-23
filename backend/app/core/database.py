from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
logger.info("Database engine configured for %s", engine.url.render_as_string(hide_password=True))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session after request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
