from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.interview import InterviewOut
from app.schemas.logs import MonitoringEventOut

class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    interview_id: str
    pdf_path: str
    integrity_score: float
    risk_level: str
    generated_at: datetime


class ReportDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    report: ReportOut
    interview: InterviewOut
    events: List[MonitoringEventOut]
    stats: dict # Dictionary holding computed aggregate stats (e.g. phone count, eye gaze %)

