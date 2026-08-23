from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./interviews.db"
    admin_session_secret: str = "local-admin-secret-change-me-32-bytes"
    invite_token_secret: str = "local-invite-secret-change-me-32b"
    canvas_token_secret: str = "local-canvas-secret-change-me-32b"
    invite_expiry_minutes: int = 60
    frontend_origins: str = "http://localhost:5173"
    ws_allowed_origins: str = "http://localhost:5173"
    canvas_sync_url: str = "http://localhost:8787"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
