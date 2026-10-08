import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./certificates.db"

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CERTIFICATES_DIR: Path = STORAGE_DIR / "certificates"
    ARCHIVES_DIR: Path = STORAGE_DIR / "archives"

    # Rate limiting & processing limits
    MAX_RECIPIENTS_PER_JOB: int = 10000
    MAX_WORKERS: int = 8

    # Defaults
    DEFAULT_ORGANIZATION: str = "Academy of Technology & Leadership"
    DEFAULT_ISSUER_NAME: str = "Dr. Victoria Sterling"
    DEFAULT_ISSUER_TITLE: str = "Director of Certification"

    # Base URL for verification links
    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_storage(self) -> None:
        """Ensure storage directories exist."""
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
        self.ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_storage()
