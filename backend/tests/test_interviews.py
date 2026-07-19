import pytest
from app.core.config import settings

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
    end_res = client.post(f"{settings.API_V1_STR}/interviews/end/{meeting_id}")
    assert end_res.status_code == 200
    assert end_res.json()["status"] == "completed"
