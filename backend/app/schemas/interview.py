from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class InterviewBase(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    scheduled_at: datetime
    duration_minutes: int = 30

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
