from .auth import router as auth
from .interviews import router as interviews
from .reports import router as reports
from .monitoring import router as monitoring

__all__ = ["auth", "interviews", "reports", "monitoring"]
