import os
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings


def get_job_directory(job_id: str) -> Path:
    """Get the specific directory where certificates for a job are stored."""
    job_dir = settings.CERTIFICATES_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def get_certificate_path(job_id: str, certificate_id: str, extension: str = "pdf") -> Path:
    """Get the full path for a certificate file."""
    job_dir = get_job_directory(job_id)
    return job_dir / f"{certificate_id}.{extension}"


def get_job_archive_path(job_id: str) -> Path:
    """Get the path for a job's bundled zip archive."""
    settings.ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
    return settings.ARCHIVES_DIR / f"certificates_job_{job_id}.zip"


def delete_job_files(job_id: str) -> None:
    """Delete all physical files associated with a job (certificates directory and archive)."""
    job_dir = settings.CERTIFICATES_DIR / job_id
    if job_dir.exists() and job_dir.is_dir():
        shutil.rmtree(job_dir, ignore_errors=True)

    archive = get_job_archive_path(job_id)
    if archive.exists() and archive.is_file():
        try:
            archive.unlink()
        except OSError:
            pass


def get_file_size_safely(path_str: Optional[str]) -> Optional[int]:
    """Return size in bytes of a file if it exists, otherwise None."""
    if not path_str:
        return None
    p = Path(path_str)
    if p.exists() and p.is_file():
        return p.stat().st_size
    return None
