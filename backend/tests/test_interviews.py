import pytest
from app.core.config import settings
from app.models.interview import Interview
from app.models.logs import MonitoringEvent
from app.models.report import Report
from app.api.interviews import generate_meeting_id


def test_new_meeting_codes_have_high_entropy():
    code = generate_meeting_id()
    assert len(code) >= 32
    assert all(character.isalnum() or character in "_-" for character in code)

def get_auth_token(client):
    # Setup user
    payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123",
        "full_name": "Test Recruiter"
    }
    client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    login_res = client.post(f"{settings.API_V1_STR}/auth/login", json={"email": "recruiter@company.com", "password": "secure_password123"})
    return login_res.json()["access_token"]


def test_schedule_interview(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    interview_payload = {
        "candidate_name": "Jane Candidate",
        "candidate_email": "jane@gmail.com",
        "scheduled_at": "2026-07-10T14:30:00Z",
        "duration_minutes": 45
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/interviews/schedule", 
        json=interview_payload,
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_name"] == "Jane Candidate"
    assert data["status"] == "scheduled"
    assert "meeting_id" in data


def test_validate_room(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Schedule room
    res = client.post(
        f"{settings.API_V1_STR}/interviews/schedule", 
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers=headers
    )
    meeting_id = res.json()["meeting_id"]

    # Public validation endpoint
    val_res = client.get(f"{settings.API_V1_STR}/interviews/validate/{meeting_id}")
    assert val_res.status_code == 200
    assert val_res.json()["meeting_id"] == meeting_id
    assert set(val_res.json()) == {"meeting_id", "candidate_name", "scheduled_at", "duration_minutes", "status"}


def test_end_interview_compilation(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Schedule
    res = client.post(
        f"{settings.API_V1_STR}/interviews/schedule", 
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers=headers
    )
    meeting_id = res.json()["meeting_id"]

    # End Meeting
    end_res = client.post(f"{settings.API_V1_STR}/interviews/end/{meeting_id}", headers=headers)
    assert end_res.status_code == 200
    assert end_res.json()["status"] == "completed"


def test_end_interview_rejects_missing_authorization(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(
        f"{settings.API_V1_STR}/interviews/schedule",
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers=headers,
    )
    meeting_id = res.json()["meeting_id"]
    response = client.post(f"{settings.API_V1_STR}/interviews/end/{meeting_id}")
    assert response.status_code == 403


def test_candidate_must_present_the_exact_invitation_code_to_end(client):
    token = get_auth_token(client)
    scheduled = client.post(
        f"{settings.API_V1_STR}/interviews/schedule",
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers={"Authorization": f"Bearer {token}"},
    )
    meeting_id = scheduled.json()["meeting_id"]

    denied = client.post(
        f"{settings.API_V1_STR}/interviews/end/{meeting_id}",
        headers={"X-Meeting-Code": "incorrect-code"},
    )
    assert denied.status_code == 403

    ended = client.post(
        f"{settings.API_V1_STR}/interviews/end/{meeting_id}",
        headers={"X-Meeting-Code": meeting_id},
    )
    assert ended.status_code == 200
    assert ended.json()["risk_level"] == "review_required"
    assert ended.json()["integrity_score"] is None


def test_non_owner_recruiter_cannot_end_interview(client):
    owner_token = get_auth_token(client)
    scheduled = client.post(
        f"{settings.API_V1_STR}/interviews/schedule",
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    meeting_id = scheduled.json()["meeting_id"]
    other_token = get_auth_token_for(client, "other-owner@company.com")

    response = client.post(
        f"{settings.API_V1_STR}/interviews/end/{meeting_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_monitoring_event_is_persisted_and_scoped_to_owner(client, db_session):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    scheduled = client.post(
        f"{settings.API_V1_STR}/interviews/schedule",
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers=headers,
    )
    interview = db_session.query(Interview).filter_by(meeting_id=scheduled.json()["meeting_id"]).one()
    db_session.add(MonitoringEvent(
        interview_id=interview.id,
        event_type="phone_detected",
        severity="high",
        details="Test observation",
    ))
    db_session.commit()

    events = client.get(f"{settings.API_V1_STR}/monitoring/events/{interview.meeting_id}", headers=headers)
    assert events.status_code == 200
    assert events.json()[0]["details"] == "Test observation"

    other_token = get_auth_token_for(client, "other@company.com")
    unauthorized = client.get(
        f"{settings.API_V1_STR}/monitoring/events/{interview.meeting_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert unauthorized.status_code == 404


def get_auth_token_for(client, email):
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": email,
        "password": "secure_password123",
        "full_name": "Other Recruiter",
    })
    response = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": email,
        "password": "secure_password123",
    })
    return response.json()["access_token"]


def test_report_download_is_scoped_to_recruiter(client, db_session):
    owner_token = get_auth_token(client)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    scheduled = client.post(
        f"{settings.API_V1_STR}/interviews/schedule",
        json={"candidate_name": "Jane", "candidate_email": "jane@gmail.com", "scheduled_at": "2026-07-10T14:30:00Z"},
        headers=owner_headers,
    )
    interview = db_session.query(Interview).filter_by(meeting_id=scheduled.json()["meeting_id"]).one()
    report = Report(interview_id=interview.id, pdf_path="missing.pdf", integrity_score=None, risk_level="review_required")
    db_session.add(report)
    db_session.commit()

    other_token = get_auth_token_for(client, "other@company.com")
    response = client.get(
        f"{settings.API_V1_STR}/reports/{report.id}/download",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404
