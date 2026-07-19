import uuid
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class MonitoringEvent(Base):
    """
    SQLAlchemy model representing a high-level incident or event log.
    Displayed on recruiter's timeline and included in report.
    """
    __tablename__ = "monitoring_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String(50), nullable=False)  # phone_detected, gaze_deviation, liveness_failed, deepfake_detected
    severity = Column(String(20), nullable=False)    # low, medium, high
    details = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    interview = relationship("Interview", back_populates="monitoring_events")


class DeepfakePrediction(Base):
    """
    SQLAlchemy model representing real-time deepfake classification metrics.
    """
    __tablename__ = "deepfake_predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Float, nullable=False)  # probability of fake
    label = Column(String(20), nullable=False)  # real, fake

    # Relationship
    interview = relationship("Interview", back_populates="deepfake_predictions")


class EyeGazeLog(Base):
    """
    SQLAlchemy model representing eye gaze tracking coordinates.
    """
    __tablename__ = "eye_gaze_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    horizontal_gaze = Column(Float, nullable=True)
    vertical_gaze = Column(Float, nullable=True)
    gaze_direction = Column(String(20), nullable=False) # left, right, center, up, down
    looking_away = Column(Boolean, default=False)
    attention_score = Column(Float, default=1.0)

    # Relationship
    interview = relationship("Interview", back_populates="eye_gaze_logs")


class PhoneDetectionLog(Base):
    """
    SQLAlchemy model representing cell phone detection metrics.
    """
    __tablename__ = "phone_detection_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    phone_detected = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)
    count = Column(Integer, default=0)

    # Relationship
    interview = relationship("Interview", back_populates="phone_detection_logs")


class LivenessLog(Base):
    """
    SQLAlchemy model representing candidate liveness checks (blinks, mouth, head movement).
    """
    __tablename__ = "liveness_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_live = Column(Boolean, default=True)
    blink_rate = Column(Float, default=0.0) # aspect ratio or counter
    head_movement_score = Column(Float, default=0.0)
    smile_score = Column(Float, default=0.0)

    # Relationship
    interview = relationship("Interview", back_populates="liveness_logs")
