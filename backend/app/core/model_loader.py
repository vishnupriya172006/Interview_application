"""Optional, explicit download of a trained deepfake model at service startup."""

from pathlib import Path
from urllib.request import urlopen

from app.core.config import settings


def ensure_deepfake_model() -> None:
    """Download MODEL_URL only when no local trained model is available."""
    model_path = Path(settings.DEEPFAKE_MODEL_PATH)
    if model_path.is_file() or not settings.MODEL_URL:
        return
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = model_path.with_suffix(model_path.suffix + ".download")
    try:
        with urlopen(settings.MODEL_URL, timeout=60) as response, temporary_path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temporary_path.replace(model_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        print("[MODEL] Unable to download the configured deepfake model.")
