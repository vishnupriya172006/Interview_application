from pathlib import Path

from pydantic import AliasChoices, Field
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
    DATABASE_URL: str = Field(
        "sqlite:///./interviewguard.db",
        validation_alias="DATABASE_URL",
    )
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
    PUBLIC_APP_URL: str = ""
    FRONTEND_URLS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    REPORTS_DIR: Path = BASE_DIR / "reports"
    MODELS_DIR: Path = BASE_DIR.parent / "models"
    DEEPFAKE_MODEL_PATH: str = str(MODELS_DIR / "deepfake_model.pth")
    YOLO_MODEL_PATH: str = str(MODELS_DIR / "yolov8n.pt")


settings = Settings()
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
