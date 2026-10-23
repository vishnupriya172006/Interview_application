from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime

class InterviewBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    candidate_name: str = Field(min_length=1, max_length=255)
    candidate_email: EmailStr
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, gt=0, le=240)

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    status: Optional[str] = None
    integrity_score: Optional[float] = None
    risk_level: Optional[str] = None

class InterviewOut(InterviewBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    recruiter_id: str
    meeting_id: str
    status: str
    integrity_score: Optional[float] = None
    risk_level: Optional[str] = None
    created_at: datetime


class InterviewJoinOut(BaseModel):
    """Minimum fields needed by the public invitation preflight screen."""
    model_config = ConfigDict(from_attributes=True)
    meeting_id: str
    candidate_name: str
    scheduled_at: datetime
    duration_minutes: int
    status: str
