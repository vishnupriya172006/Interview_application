from pathlib import Path
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "InterviewGuard AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    # SQLite is retained only for a zero-configuration local run and the test
    # suite. Docker Compose and every production deployment provide PostgreSQL.
    DATABASE_URL: str = Field("sqlite:///./interviewguard.db", validation_alias="DATABASE_URL")
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = Field(
        "change-this-secret-key-before-production",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"),
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@interviewguard.ai"
    FRONTEND_BASE_URL: str = Field("", validation_alias=AliasChoices("FRONTEND_BASE_URL", "PUBLIC_APP_URL"))
    INTERVIEW_BASE_URL: str = ""
    FRONTEND_URLS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    REPORTS_DIR: Path = BASE_DIR / "reports"
    MODELS_DIR: Path = BASE_DIR.parent / "models"
    # MODEL_PATH is the trained deepfake classifier. It is intentionally not
    # substituted with random weights when absent.
    DEEPFAKE_MODEL_PATH: str = Field(str(MODELS_DIR / "deepfake_model.pth"), validation_alias=AliasChoices("DEEPFAKE_MODEL_PATH", "MODEL_PATH"))
    MODEL_URL: str = ""
    YOLO_MODEL_PATH: str = str(MODELS_DIR / "yolov8n.pt")

    @field_validator("FRONTEND_URLS", mode="before")
    @classmethod
    def parse_frontend_urls(cls, value):
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql://", 1)


def _is_https_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and parsed.password is None
    except ValueError:
        return False


def validate_production_settings(config: Settings) -> None:
    if config.ENVIRONMENT.strip().lower() != "production":
        return
    if not config.DATABASE_URL.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL URL when ENVIRONMENT=production.")

    secret = config.SECRET_KEY.strip()
    lowered_secret = secret.lower()
    if len(secret) < 32 or any(
        marker in lowered_secret
        for marker in ("change-this", "replace-with", "your-secret", "example")
    ):
        raise RuntimeError("SECRET_KEY must be a non-default secret with at least 32 characters in production.")

    if not config.FRONTEND_BASE_URL or not _is_https_url(config.FRONTEND_BASE_URL):
        raise RuntimeError("FRONTEND_BASE_URL must be an HTTPS URL in production.")
    if config.INTERVIEW_BASE_URL and not _is_https_url(config.INTERVIEW_BASE_URL):
        raise RuntimeError("INTERVIEW_BASE_URL must be an HTTPS URL in production.")
    if not config.FRONTEND_URLS or any(not _is_https_url(origin) for origin in config.FRONTEND_URLS):
        raise RuntimeError("Every FRONTEND_URLS origin must use HTTPS in production.")


validate_production_settings(settings)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
