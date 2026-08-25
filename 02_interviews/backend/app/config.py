from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./interviews.db"
    admin_session_secret: str = "local-admin-secret-change-me-32-bytes"
    invite_token_secret: str = "local-invite-secret-change-me-32b"
    canvas_token_secret: str = "local-canvas-secret-change-me-32b"
    invite_expiry_minutes: int = 60
    frontend_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"
    ws_allowed_origins: str = "http://localhost:5173"
    canvas_sync_url: str = "http://localhost:8787"
    app_session_ttl_minutes: int = 60
    app_cookie_secure: bool = False
    app_cookie_domain: str | None = None
    google_client_id: str = ""
    google_allowed_domains: str = ""
    google_provider_mode: str = "disabled"
    google_public_key: str = ""
    google_issuer: str = "https://accounts.google.com"
    google_auto_approve: bool = False
    recaptcha_mode: str = "mock"
    recaptcha_secret: str = ""
    recaptcha_allowed_hostnames: str = ""
    recaptcha_allow_score: float = 0.7
    recaptcha_stepup_score: float = 0.4
    recaptcha_max_age_seconds: int = 120
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
