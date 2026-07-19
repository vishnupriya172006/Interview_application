import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    """
    SQLAlchemy model representing recruiters/users who conduct interviews.
    """
    __tablename__ = "users"

    # Support PostgreSQL UUID if available, else fall back to a String representation
    # UUID string length is 36 characters (including hyphens)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    interviews = relationship("Interview", back_populates="recruiter", cascade="all, delete-orphan")
