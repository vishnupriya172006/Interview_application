import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview
from app.models.report import Report
from app.models.logs import MonitoringEvent, DeepfakePrediction, EyeGazeLog, PhoneDetectionLog, LivenessLog
from app.schemas.report import ReportOut, ReportDetailOut

router = APIRouter()

@router.get("/", response_model=List[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all generated integrity reports for interviews conducted by the logged in recruiter.
    """
    return db.query(Report).join(Interview).filter(
        Interview.recruiter_id == current_user.id
    ).order_by(Report.generated_at.desc()).all()


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report_details(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches comprehensive logs and metrics for an interview report to render custom dashboard visualizations.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
        
    interview = db.query(Interview).filter(
        Interview.id == report.interview_id,
        Interview.recruiter_id == current_user.id
    ).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Report not found.")
        
    # Get all logs to compile UI statistics
    events = db.query(MonitoringEvent).filter_by(interview_id=interview.id).order_by(MonitoringEvent.timestamp).all()
    deepfake_logs = db.query(DeepfakePrediction).filter_by(interview_id=interview.id).all()
    gaze_logs = db.query(EyeGazeLog).filter_by(interview_id=interview.id).all()
    phone_logs = db.query(PhoneDetectionLog).filter_by(interview_id=interview.id).all()
    liveness_logs = db.query(LivenessLog).filter_by(interview_id=interview.id).all()
    
    # Calculate stats
    avg_deepfake = (sum(l.score for l in deepfake_logs) / len(deepfake_logs)) if deepfake_logs else None
    gaze_away = sum(1 for l in gaze_logs if l.looking_away)
    gaze_total = len(gaze_logs)
    phone_count = sum(1 for l in phone_logs if l.phone_detected)
    liveness_fail = sum(1 for l in liveness_logs if not l.is_live)
    
    stats = {
        "avg_deepfake": round(avg_deepfake * 100, 1) if avg_deepfake is not None else None,
        "gaze_away_ratio": round((gaze_away / gaze_total) * 100, 1) if gaze_total else None,
        "phone_detections": phone_count,
        "liveness_anomalies": liveness_fail,
        "total_frames": max(len(deepfake_logs), len(gaze_logs), len(phone_logs), len(liveness_logs)),
        "analysis_status": {
            "deepfake": "analyzed" if deepfake_logs else "unavailable_or_no_samples",
            "gaze": "analyzed" if gaze_logs else "unavailable_or_no_samples",
            "phone": "analyzed" if phone_logs else "unavailable_or_no_samples",
            "liveness": "analyzed" if liveness_logs else "unavailable_or_no_samples",
        },
    }
    
    return {
        "report": report,
        "interview": interview,
        "events": events,
        "stats": stats
    }


@router.get("/{report_id}/download")
def download_report_pdf(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads the compiled PDF integrity report file.
    Only the recruiter who owns the interview may download its report.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if not db.query(Interview).filter(
        Interview.id == report.interview_id,
        Interview.recruiter_id == current_user.id,
    ).first():
        raise HTTPException(status_code=404, detail="Report not found.")
        
    if not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file was not found on disk.")
        
    filename = os.path.basename(report.pdf_path)
    return FileResponse(
        report.pdf_path, 
        media_type='application/pdf', 
        filename=filename
    )
