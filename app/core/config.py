"""Configuration module for the WhisperX FastAPI application."""

from functools import lru_cache
from typing import Any, Optional

import torch
from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas import ComputeType, Device, WhisperModel


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    DB_URL: str = Field(
        default="sqlite:///records.db",
        description="Database connection URL",
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries for debugging",
    )


class WhisperSettings(BaseSettings):
    """WhisperX ML model configuration settings."""

    HF_TOKEN: Optional[str] = Field(
        default=None,
        description="HuggingFace API token for model downloads",
    )
    WHISPER_MODEL: WhisperModel = Field(
        default=WhisperModel.tiny,
        description="Whisper model size to use",
    )
    DEFAULT_LANG: str = Field(
        default="en",
        description="Default language for transcription",
    )
    DEVICE: Device = Field(
        default_factory=lambda: Device.cuda
        if torch.cuda.is_available()
        else Device.cpu,
        description="Device to use for computation (cuda or cpu)",
    )
    COMPUTE_TYPE: ComputeType = Field(
        default_factory=lambda: (
            ComputeType.float16 if torch.cuda.is_available() else ComputeType.int8
        ),
        description="Compute type for model inference",
    )

    AUDIO_EXTENSIONS: set[str] = {
        ".mp3",
        ".wav",
        ".awb",
        ".aac",
        ".ogg",
        ".oga",
        ".m4a",
        ".wma",
        ".amr",
    }
    VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".wmv", ".mkv"}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ALLOWED_EXTENSIONS(self) -> set[str]:
        """Compute allowed extensions by combining audio and video."""
        return self.AUDIO_EXTENSIONS | self.VIDEO_EXTENSIONS

    @model_validator(mode="after")
    def validate_compute_type_for_cpu(self) -> "WhisperSettings":
        """Validate that CPU device uses int8 compute type."""
        if self.DEVICE == Device.cpu and self.COMPUTE_TYPE != ComputeType.int8:
            # Auto-correct instead of raising error
            self.COMPUTE_TYPE = ComputeType.int8
        return self


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    LOG_FORMAT: str = Field(
        default="text",
        description="Log format: text or json",
    )
    FILTER_WARNING: bool = Field(
        default=True,
        description="Filter specific warnings",
    )


class CORSSettings(BaseSettings):
    """CORS (Cross-Origin Resource Sharing) configuration settings."""

    CORS_ORIGINS: Any = Field(
        default=["*"],
        description="List of allowed origins for CORS. Use ['*'] to allow all origins.",
    )
    CORS_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials (cookies, authorization headers) in CORS requests",
    )
    CORS_METHODS: Any = Field(
        default=["*"],
        description="List of allowed HTTP methods for CORS",
    )
    CORS_HEADERS: Any = Field(
        default=["*"],
        description="List of allowed HTTP headers for CORS",
    )

    @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_cors_list(cls, v: Any) -> list[str]:
        """Parse CORS fields from string, list, or None."""
        # Handle None or empty string
        if v is None or v == "":
            return ["*"]
        # Already a list
        if isinstance(v, list):
            return v if v else ["*"]
        # Parse string (comma-separated or single value)
        if isinstance(v, str):
            # Handle wildcard
            if v.strip() == "*":
                return ["*"]
            # Split comma-separated values
            items = [item.strip() for item in v.split(",") if item.strip()]
            return items if items else ["*"]
        # Fallback
        return ["*"]


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_nested_delimiter="__",
    )

    ENVIRONMENT: str = Field(
        default="production",
        description="Environment: development, testing, production",
    )
    DEV: bool = Field(
        default=False,
        description="Development mode flag",
    )

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    whisper: WhisperSettings = Field(default_factory=WhisperSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        """Normalize environment to lowercase."""
        return str(v).lower() if v else "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).

    Returns:
        Settings: The application settings instance.
    """
    return Settings()


# Legacy Config class for backward compatibility during migration
# This will be removed once all references are updated
class Config:
    """DEPRECATED: Legacy configuration class. Use get_settings() instead."""

    _settings = get_settings()

    # Delegate to new settings
    LANG = _settings.whisper.DEFAULT_LANG
    HF_TOKEN = _settings.whisper.HF_TOKEN
    WHISPER_MODEL = _settings.whisper.WHISPER_MODEL
    DEVICE = _settings.whisper.DEVICE
    COMPUTE_TYPE = _settings.whisper.COMPUTE_TYPE
    ENVIRONMENT = _settings.ENVIRONMENT
    LOG_LEVEL = _settings.logging.LOG_LEVEL
    AUDIO_EXTENSIONS = _settings.whisper.AUDIO_EXTENSIONS
    VIDEO_EXTENSIONS = _settings.whisper.VIDEO_EXTENSIONS
    ALLOWED_EXTENSIONS = _settings.whisper.ALLOWED_EXTENSIONS
    DB_URL = _settings.database.DB_URL
