import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Report(Base):
    """
    SQLAlchemy model representing the final integrity assessment PDF report.
    """
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    pdf_path = Column(String(500), nullable=False)
    integrity_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False) # low, medium, high
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    interview = relationship("Interview", back_populates="reports")
