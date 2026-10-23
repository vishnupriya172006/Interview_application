from types import SimpleNamespace

import pytest

from app.core.config import validate_production_settings


def _production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql://db.example/interviewguard",
        "SECRET_KEY": "a" * 48,
        "FRONTEND_BASE_URL": "https://app.example.com",
        "INTERVIEW_BASE_URL": "https://app.example.com",
        "FRONTEND_URLS": ["https://app.example.com"],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_valid_production_configuration_is_accepted():
    validate_production_settings(_production_settings())


@pytest.mark.parametrize("secret", [
    "change-this-secret-key-before-production",
    "replace-with-a-long-random-secret-value",
    "short",
])
def test_production_rejects_default_or_short_jwt_secret(secret):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_settings(_production_settings(SECRET_KEY=secret))


@pytest.mark.parametrize("field", ["FRONTEND_BASE_URL", "INTERVIEW_BASE_URL"])
def test_production_requires_secure_frontend_urls(field):
    with pytest.raises(RuntimeError, match="HTTPS"):
        validate_production_settings(_production_settings(**{field: "http://app.example.com"}))


def test_production_rejects_non_https_frontend_origin():
    with pytest.raises(RuntimeError, match="FRONTEND_URLS"):
        validate_production_settings(_production_settings(FRONTEND_URLS=["http://app.example.com"]))


def test_production_rejects_urls_with_embedded_credentials():
    with pytest.raises(RuntimeError, match="FRONTEND_BASE_URL"):
        validate_production_settings(_production_settings(
            FRONTEND_BASE_URL="https://user:password@app.example.com"
        ))
