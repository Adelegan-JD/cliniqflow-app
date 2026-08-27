from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_environment: str = "development"
    backend_port: int = 8000
    database_url: str = ""
    supabase_url: str = ""
    # JWT secret from Supabase project Settings → API → JWT Secret (HS256)
    supabase_jwt_secret: str = ""
    # Optional explicit issuer/JWKS settings (for asymmetric signing setups)
    supabase_jwt_issuer: str | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_verify_aud: bool = True
    supabase_service_role_key: str = ""
    ai_engine_url: str = "http://127.0.0.1:8001"
    # Internal shared token for backend -> AI-engine calls. Configure this in
    # each environment; it is unrelated to any paid AI provider key.
    ai_engine_token: str = ""
    # Comma-separated origins for CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # When true, accept any Bearer token and use X-Debug-Role / X-Debug-User-Id (local only)
    # Keep this OFF by default so production always uses real authentication.
    cliniq_dev_bypass_auth: bool = False

    @property
    def is_production(self) -> bool:
        return self.app_environment.strip().lower() in {"production", "prod"}

    def validate_production(self) -> None:
        """Fail early instead of serving clinical data with a weak setup."""
        if not self.is_production:
            return
        missing = []
        if not self.database_url:
            missing.append("DATABASE_URL")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_jwt_secret and not self.supabase_jwks_url:
            missing.append("SUPABASE_JWT_SECRET or SUPABASE_JWKS_URL")
        if not self.ai_engine_token:
            missing.append("AI_ENGINE_TOKEN")
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins:
            missing.append("CORS_ORIGINS")
        invalid_origins = [origin for origin in origins if not origin.startswith("https://")]
        if missing or invalid_origins or self.cliniq_dev_bypass_auth:
            invalid_detail = ([f"CORS_ORIGINS must use HTTPS (invalid: {', '.join(invalid_origins)})"] if invalid_origins else [])
            problems = ", ".join(missing + (["CLINIQ_DEV_BYPASS_AUTH must be false"] if self.cliniq_dev_bypass_auth else []))
            problems = ", ".join(part for part in (problems, *invalid_detail) if part)
            raise RuntimeError(f"Unsafe production configuration: {problems}")

    @property
    def resolved_supabase_jwt_issuer(self) -> str:
        return self.supabase_jwt_issuer or f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def resolved_supabase_jwks_url(self) -> str:
        return self.supabase_jwks_url or f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


settings = Settings()
