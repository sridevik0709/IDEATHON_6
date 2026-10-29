"""
Configuration management using Pydantic Settings.
Enforces validation on environment variables and provides sensible defaults for development.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = Field(default="GRIDGUARD NEXUS X", description="Platform name")
    PROJECT_VERSION: str = Field(default="3.0.0-level3", description="Current release version")
    STAGE: str = Field(default="LEVEL 3: CORE ELECTRICITY INTELLIGENCE", description="Platform development phase")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment: development/testing/production")
    DEBUG: bool = Field(default=True, description="Debug mode flag")

    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    HOST: str = Field(default="0.0.0.0", description="Backend host binding")
    PORT: int = Field(default=8000, description="Backend port binding")

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )

    # Database Configuration (PostgreSQL persistent storage)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection string (e.g. postgresql+psycopg://user:password@localhost:5432/gridguard)"
    )
    DATABASE_TIMEOUT_SECONDS: int = Field(default=5, description="Timeout for database probe operations")
    DATABASE_DEV_FALLBACK_SQLITE: bool = Field(
        default=True,
        description="Fallback to local SQLite engine during development if PostgreSQL is not provisioned"
    )

    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-gridguard-nexus-x-level-1-foundation", description="Cryptographic secret key")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, v):
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("release", "prod", "production", "false", "0", "no", "off"):
                return False
            if v_lower in ("debug", "dev", "development", "true", "1", "yes", "on"):
                return True
        return bool(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


# Cached global settings instance
settings = Settings()
