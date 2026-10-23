import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.security import decode_access_token
from app.models.interview import Interview
from app.schemas.interview import InterviewCreate, InterviewOut, InterviewJoinOut
from app.services.email import send_interview_invitation
from app.services.pdf_generator import generate_pdf_report

router = APIRouter()

def generate_meeting_id() -> str:
    """Generate a high-entropy invitation code; the code is a bearer credential."""
    return secrets.token_urlsafe(24)


@router.post("/schedule", response_model=InterviewOut)
def schedule_interview(
    interview_in: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Schedules an interview, stores it in DB, and fires SMTP/mock invitation email.
    """
    # Keep generating meeting IDs until unique
    meeting_id = generate_meeting_id()
    while db.query(Interview).filter(Interview.meeting_id == meeting_id).first() is not None:
        meeting_id = generate_meeting_id()
        
    db_interview = Interview(
        recruiter_id=current_user.id,
        candidate_name=interview_in.candidate_name,
        candidate_email=interview_in.candidate_email,
        meeting_id=meeting_id,
        scheduled_at=interview_in.scheduled_at,
        duration_minutes=interview_in.duration_minutes,
        status="scheduled"
    )
    
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    
    # Send email invitation (SMTP helper)
    send_interview_invitation(
        candidate_name=db_interview.candidate_name,
        candidate_email=db_interview.candidate_email,
        meeting_id=db_interview.meeting_id,
        scheduled_at=db_interview.scheduled_at.strftime('%Y-%m-%d %H:%M UTC'),
        duration_minutes=db_interview.duration_minutes
    )
    
    return db_interview


@router.get("/", response_model=List[InterviewOut])
def list_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all scheduled, active, or completed interviews for the logged in recruiter.
    """
    return db.query(Interview).filter(Interview.recruiter_id == current_user.id).order_by(Interview.scheduled_at.desc()).all()


@router.get("/validate/{meeting_id}", response_model=InterviewJoinOut)
def validate_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """
    Public validation endpoint.
    Checks if a meeting room exists and is joinable. Used by candidate & recruiter frontends.
    """
    interview = db.query(Interview).filter(Interview.meeting_id == meeting_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview meeting room not found."
        )
    if interview.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This interview has already completed."
        )
    if interview.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This interview has been cancelled."
        )
    return interview


@router.post("/end/{meeting_id}", response_model=InterviewOut)
def end_interview(
    meeting_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Ends the interview, changes state to 'completed', and compiles the PDF integrity report.
    The candidate may end their own meeting by presenting its invitation code.
    """
    interview = db.query(Interview).filter(Interview.meeting_id == meeting_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    # The candidate invitation is a capability for this one meeting. Recruiters
    # must present a valid JWT belonging to the interview owner.
    invitation_code = request.headers.get("x-meeting-code")
    authorization = request.headers.get("authorization", "")
    subject = decode_access_token(authorization.removeprefix("Bearer ")) if authorization.startswith("Bearer ") else None
    owner = db.query(User).filter(User.id == subject).first() if subject else None
    if owner is None and subject:
        owner = db.query(User).filter(User.email == subject).first()
    if (owner is None or owner.id != interview.recruiter_id) and invitation_code != meeting_id:
        raise HTTPException(status_code=403, detail="Meeting authorization required.")
        
    if interview.status == "completed":
        return interview
        
    interview.status = "completed"
    db.commit()
    
    # Generate the automated PDF integrity report
    try:
        generate_pdf_report(interview, db)
    except Exception as e:
        print(f"Error building integrity report PDF: {e}")
        
    return interview


@router.get("/{meeting_id}", response_model=InterviewOut)
def get_interview(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single interview's data.
    """
    interview = db.query(Interview).filter(
        Interview.meeting_id == meeting_id,
        Interview.recruiter_id == current_user.id
    ).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized access.")
    return interview
