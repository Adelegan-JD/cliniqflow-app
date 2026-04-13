from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    backend_port: int = 8000
    supabase_url: str = "https://example.supabase.co"
    # JWT secret from Supabase project Settings → API → JWT Secret (HS256)
    supabase_jwt_secret: str = "dev-insecure-change-me"
    supabase_jwt_verify_aud: bool = True
    ai_engine_url: str = "http://127.0.0.1:8001"
    ai_engine_token: str = "change-me-in-production"
    # Comma-separated origins for CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # When true, accept any Bearer token and use X-Debug-Role / X-Debug-User-Id (local only)
    cliniq_dev_bypass_auth: bool = False


settings = Settings()
