"""Settings and configuration for JobSleuth AI backend."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")
    PRICE_ID_PRO: str = os.getenv("PRICE_ID_PRO", "")
    PRICE_ID_INVESTOR: str = os.getenv("PRICE_ID_INVESTOR", "")

    # OpenAI
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

    # Email
    RESEND_API_KEY: str | None = os.getenv("RESEND_API_KEY")
    MAILGUN_API_KEY: str | None = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN: str | None = os.getenv("MAILGUN_DOMAIN")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@jobsleuth.ai")

    # Scraping
    PROVIDER_API_KEY: str | None = os.getenv("PROVIDER_API_KEY")
    SCRAPE_PROVIDER: str = os.getenv("SCRAPE_PROVIDER", "off")
    FEATURE_SCRAPE_INTERNAL: bool = os.getenv("FEATURE_SCRAPE_INTERNAL", "false").lower() == "true"
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    PROXY_URL: str | None = os.getenv("PROXY_URL")

    # Auth
    AUTH_SCRAPER_KEY: str = os.getenv("AUTH_SCRAPER_KEY", "change-me-in-production")

    # API
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


settings = Settings()
