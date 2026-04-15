import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    google_credentials_path: Path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
    google_oauth_client_config_json: str | None = os.getenv("GOOGLE_OAUTH_CLIENT_CONFIG_JSON")
    google_client_id: str | None = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    frontend_post_auth_url: str = os.getenv("FRONTEND_POST_AUTH_URL", "http://localhost:5173")
    public_backend_url: str = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-in-production")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    session_same_site: str = os.getenv("SESSION_SAME_SITE", "lax")
    allow_insecure_oauth_transport: bool = os.getenv("ALLOW_INSECURE_OAUTH_TRANSPORT", "true").lower() == "true"

    def has_google_oauth_config(self) -> bool:
        return bool(
            self.google_oauth_client_config_json
            or (self.google_client_id and self.google_client_secret)
            or self.google_credentials_path.exists()
        )


settings = Settings()
