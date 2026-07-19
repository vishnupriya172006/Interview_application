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
