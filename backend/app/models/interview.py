import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Interview(Base):
    """
    SQLAlchemy model representing scheduled and completed interviews.
    """
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID string length is 36
    recruiter_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    meeting_id = Column(String(255), unique=True, index=True, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(50), default="scheduled")  # scheduled, active, completed, cancelled
    integrity_score = Column(Float, nullable=True) # Computed at the end
    risk_level = Column(String(50), nullable=True)      # low, medium, high
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    recruiter = relationship("User", back_populates="interviews")
    
    monitoring_events = relationship("MonitoringEvent", back_populates="interview", cascade="all, delete-orphan")
    deepfake_predictions = relationship("DeepfakePrediction", back_populates="interview", cascade="all, delete-orphan")
    eye_gaze_logs = relationship("EyeGazeLog", back_populates="interview", cascade="all, delete-orphan")
    phone_detection_logs = relationship("PhoneDetectionLog", back_populates="interview", cascade="all, delete-orphan")
    liveness_logs = relationship("LivenessLog", back_populates="interview", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="interview", cascade="all, delete-orphan")
