import pytest
from app.core.config import settings

def test_register_recruiter(client):
    payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123",
        "full_name": "Test Recruiter",
        "company_name": "Test Company"
      }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "recruiter@company.com"
    assert "id" in data
    assert "hashed_password" not in data

def test_login_recruiter(client):
    # First register user
    payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123",
        "full_name": "Test Recruiter",
        "company_name": "Test Company"
    }
    client.post(f"{settings.API_V1_STR}/auth/register", json=payload)

    # Perform login
    login_payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123"
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "recruiter@company.com"

def test_login_incorrect_password(client):
    payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123",
        "full_name": "Test Recruiter"
    }
    client.post(f"{settings.API_V1_STR}/auth/register", json=payload)

    login_payload = {
        "email": "recruiter@company.com",
        "password": "wrongpassword"
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", json=login_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

def test_register_duplicate_email(client):
    payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123",
        "full_name": "Test Recruiter"
    }
    # Register first time
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert response.status_code == 201

    # Register second time
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_access_token_cannot_be_used_as_password_reset_token(client):
    payload = {
        "email": "recruiter@company.com",
        "password": "secure_password123",
        "full_name": "Test Recruiter",
    }
    client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    login = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": payload["email"],
        "password": payload["password"],
    }).json()
    response = client.post(f"{settings.API_V1_STR}/auth/reset-password", json={
        "token": login["access_token"],
        "new_password": "new_secure_password123",
    })
    assert response.status_code == 400


def test_password_recovery_does_not_claim_email_was_sent(client):
    response = client.post(f"{settings.API_V1_STR}/auth/forgot-password", json={"email": "person@example.com"})
    assert response.status_code == 200
    assert "if the address matches" in response.json()["message"].lower()


def test_password_recovery_sends_reset_only_token_without_returning_it(client, monkeypatch):
    import importlib
    auth = importlib.import_module("app.api.auth")
    from app.core.security import decode_access_token

    email = "recruiter@company.com"
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": email,
        "password": "secure_password123",
        "full_name": "Test Recruiter",
    })
    sent = []
    monkeypatch.setattr(auth, "send_password_reset_email", lambda address, token: sent.append((address, token)) or True)

    response = client.post(f"{settings.API_V1_STR}/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert email not in response.text
    assert len(sent) == 1
    assert sent[0][0] == email
    assert decode_access_token(sent[0][1]) is None
    assert decode_access_token(sent[0][1], expected_use="password_reset") == email


def test_password_reset_token_can_reset_password(client):
    from datetime import timedelta
    from app.core.security import create_access_token

    email = "recruiter@company.com"
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": email,
        "password": "secure_password123",
        "full_name": "Test Recruiter",
    })
    reset_token = create_access_token(
        email,
        expires_delta=timedelta(hours=1),
        token_use="password_reset",
    )
    reset = client.post(f"{settings.API_V1_STR}/auth/reset-password", json={
        "token": reset_token,
        "new_password": "updated_password123",
    })
    assert reset.status_code == 200
    login = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": email,
        "password": "updated_password123",
    })
    assert login.status_code == 200
