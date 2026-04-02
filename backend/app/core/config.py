"""
Configuration management for the Energy Dashboard application
"""
import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_name: str = Field(default="Energy Dashboard", validation_alias="APP_NAME")
    app_version: str = Field(default="1.0.0", validation_alias="APP_VERSION")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # API Server
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    api_reload: bool = Field(default=True, validation_alias="API_RELOAD")
    frontend_url: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_URL")

    # Database
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    database_echo: bool = Field(default=False, validation_alias="SQLALCHEMY_ECHO")

    # SharePoint
    sharepoint_tenant_id: Optional[str] = Field(default=None, validation_alias="SHAREPOINT_TENANT_ID")
    sharepoint_client_id: Optional[str] = Field(default=None, validation_alias="SHAREPOINT_CLIENT_ID")
    sharepoint_client_secret: Optional[str] = Field(default=None, validation_alias="SHAREPOINT_CLIENT_SECRET")
    sharepoint_site_url: Optional[str] = Field(default=None, validation_alias="SHAREPOINT_SITE_URL")
    sharepoint_list_id: Optional[str] = Field(default=None, validation_alias="SHAREPOINT_LIST_ID")

    # Google Sheets
    google_application_credentials: Optional[str] = Field(default=None, validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    google_sheet_id: Optional[str] = Field(default=None, validation_alias="GOOGLE_SHEET_ID")
    google_sheet_range: str = Field(default="Sheet1!A1:Z1000", validation_alias="GOOGLE_SHEET_RANGE")

    # Email
    smtp_server: Optional[str] = Field(default=None, validation_alias="SMTP_SERVER")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, validation_alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, validation_alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, validation_alias="SMTP_USE_TLS")

    # Scheduling
    schedule_ingestion_daily: str = Field(default="09:00", validation_alias="SCHEDULE_INGESTION_DAILY")
    schedule_email_daily: str = Field(default="18:00", validation_alias="SCHEDULE_EMAIL_DAILY")
    timezone: str = Field(default="UTC", validation_alias="TIMEZONE")

    # Data Ingestion
    data_ingestion_timeout: int = Field(default=3600, validation_alias="DATA_INGESTION_TIMEOUT")
    data_cache_expiry: int = Field(default=3600, validation_alias="DATA_CACHE_EXPIRY")
    data_retention_days: int = Field(default=90, validation_alias="DATA_RETENTION_DAYS")

    # API Keys
    groq_api_key: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="ALLOWED_ORIGINS",
    )

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, validation_alias="SENTRY_DSN")
    log_file_path: str = Field(default="./backend/logs/app.log", validation_alias="LOG_FILE_PATH")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env.lower() == "development"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins as list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings instance
    """
    return Settings()
