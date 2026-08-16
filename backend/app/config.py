"""Application configuration using pydantic-settings."""

from enum import StrEnum

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(StrEnum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(StrEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class EmbeddingProvider(StrEnum):
    """Supported embedding providers (independent of LLM provider)."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    CUSTOM = "custom"



class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codegraph"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # LLM settings
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"

    # Embedding settings (independent of LLM provider)
    EMBEDDING_PROVIDER: EmbeddingProvider = EmbeddingProvider.OPENAI
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # Authentication
    REQUIRE_AUTH: bool = False
    REQUIRE_AUTH_FOR_READS: bool = False
    ADMIN_API_KEY: str = ""

    # Repository limits
    MAX_REPO_SIZE_MB: int = 500

    # Storage
    UPLOAD_DIR: str = "./uploads"

    # Application
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str] | object:
        """Parse comma-separated CORS origins string into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == EnvironmentType.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == EnvironmentType.PRODUCTION


def get_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()
