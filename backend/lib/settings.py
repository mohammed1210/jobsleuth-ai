"""Settings and configuration for JobSleuth AI backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    NEXT_PUBLIC_STRIPE_PRICE_PRO: str = "price_pro_xxx"
    NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS: str = "price_career_plus_xxx"
    NEXT_PUBLIC_STRIPE_PRICE_INVESTOR: str = "price_investor_xxx"

    OPENAI_API_KEY: str | None = None

    EMAIL_SERVER: str | None = None
    EMAIL_USER: str | None = None
    EMAIL_PASSWORD: str | None = None
    EMAIL_FROM: str = "noreply@jobsleuth.ai"

    PROVIDER_API_KEY: str | None = None
    SCRAPE_PROVIDER: str = "off"
    FEATURE_SCRAPE_INTERNAL: bool = False
    HEADLESS: bool = True
    PROXY_URL: str | None = None

    AUTH_SCRAPER_KEY: str = "change-me-in-production"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: str = ""
    ENABLE_DEBUG_ROUTES: bool = False


settings = Settings()
