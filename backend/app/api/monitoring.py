from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.interview import Interview
from app.models.logs import MonitoringEvent, DeepfakePrediction, EyeGazeLog, PhoneDetectionLog, LivenessLog
from app.schemas.logs import MonitoringEventOut, DeepfakePredictionOut, EyeGazeLogOut, PhoneDetectionLogOut, LivenessLogOut

router = APIRouter()

@router.get("/events/{meeting_id}", response_model=List[MonitoringEventOut])
def get_monitoring_events(meeting_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    interview = db.query(Interview).filter(Interview.meeting_id == meeting_id, Interview.recruiter_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")
    return db.query(MonitoringEvent).filter(MonitoringEvent.interview_id == interview.id).order_by(MonitoringEvent.timestamp).all()

@router.get("/metrics/{meeting_id}")
def get_monitoring_metrics(meeting_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    interview = db.query(Interview).filter(Interview.meeting_id == meeting_id, Interview.recruiter_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")
    deepfake = db.query(DeepfakePrediction).filter(DeepfakePrediction.interview_id == interview.id).order_by(DeepfakePrediction.timestamp.desc()).limit(20).all()
    gaze = db.query(EyeGazeLog).filter(EyeGazeLog.interview_id == interview.id).order_by(EyeGazeLog.timestamp.desc()).limit(20).all()
    phone = db.query(PhoneDetectionLog).filter(PhoneDetectionLog.interview_id == interview.id).order_by(PhoneDetectionLog.timestamp.desc()).limit(20).all()
    liveness = db.query(LivenessLog).filter(LivenessLog.interview_id == interview.id).order_by(LivenessLog.timestamp.desc()).limit(20).all()
    return {
        "deepfake": [DeepfakePredictionOut.model_validate(item).model_dump(mode="json") for item in deepfake],
        "gaze": [EyeGazeLogOut.model_validate(item).model_dump(mode="json") for item in gaze],
        "phone": [PhoneDetectionLogOut.model_validate(item).model_dump(mode="json") for item in phone],
        "liveness": [LivenessLogOut.model_validate(item).model_dump(mode="json") for item in liveness],
    }
