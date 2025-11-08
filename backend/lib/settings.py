"""
Settings and configuration management for JobSleuth AI backend.

Uses pydantic-settings for type-safe configuration from environment variables.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    DATABASE_URL: str = "postgresql://localhost/jobsleuth"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # AI/ML
    OPENAI_API_KEY: Optional[str] = None
    
    # Email
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "noreply@jobsleuth.ai"
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PRICE_ID_PRO: str = ""
    PRICE_ID_INVESTOR: str = ""
    
    # Scraping
    PROVIDER_API_KEY: Optional[str] = None
    SCRAPE_PROVIDER: str = "off"
    HEADLESS: bool = True
    PROXY_URL: Optional[str] = None
    
    # Auth
    AUTH_SCRAPER_KEY: str = ""
    
    # Feature Flags
    FEATURE_AI_FIT: bool = False
    FEATURE_RESUME_TOOLS: bool = False
    FEATURE_DIGESTS: bool = False
    FEATURE_SCRAPE_INTERNAL: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
