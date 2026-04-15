import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    google_credentials_path: Path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    frontend_post_auth_url: str = os.getenv("FRONTEND_POST_AUTH_URL", "http://localhost:5173")
    public_backend_url: str = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-in-production")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    session_same_site: str = os.getenv("SESSION_SAME_SITE", "lax")
    allow_insecure_oauth_transport: bool = os.getenv("ALLOW_INSECURE_OAUTH_TRANSPORT", "true").lower() == "true"


settings = Settings()
