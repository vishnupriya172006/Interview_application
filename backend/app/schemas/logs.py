from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class MonitoringEventBase(BaseModel):
    event_type: str
    severity: str
    details: Optional[str] = None

class MonitoringEventCreate(MonitoringEventBase):
    pass

class MonitoringEventOut(MonitoringEventBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    interview_id: str
    timestamp: datetime


class DeepfakePredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime
    score: float
    label: str


class EyeGazeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime
    gaze_direction: str
    looking_away: bool
    attention_score: float


class PhoneDetectionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime
    phone_detected: bool
    confidence: float
    count: int


class LivenessLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime
    is_live: bool
    blink_rate: float
    head_movement_score: float
    smile_score: float


class RealTimeAIFramePayload(BaseModel):
    """
    Format of payload received from Candidate's webcam frame stream
    via Socket.IO or REST.
    """
    frame_base64: str # Base64 encoded JPEG image

class RealTimeAIResponse(BaseModel):
    """
    Metrics computed by AI for a single frame, sent to Recruiter dashboard.
    """
    deepfake_score: float
    liveness_status: bool
    gaze_direction: str
    looking_away: bool
    phone_detected: bool
    phone_count: int
    integrity_score: float
    bbox: Optional[List[int]] = None # Bounding box [x, y, w, h] of face or phone
