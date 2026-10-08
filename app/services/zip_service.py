import os
import re
import zipfile
from pathlib import Path
from typing import Optional

from app.models.certificate import Certificate, CertificateStatus
from app.utils.file_manager import get_job_archive_path


def sanitize_filename(name: str) -> str:
    """Sanitize string for safe filenames across OSes."""
    clean = re.sub(r'[\\/*?:"<>|]', "_", name)
    clean = re.sub(r"\s+", "_", clean).strip("_")
    return clean or "certificate"


class ZipService:
    """Service to create zip archives of generated certificates for bulk download."""

    @classmethod
    def create_job_archive(cls, job_id: str, certificates: list[Certificate], force_recreate: bool = False) -> Optional[Path]:
        """
        Create a ZIP archive containing all successfully generated certificates for a job.
        """
        archive_path = get_job_archive_path(job_id)

        if archive_path.exists() and not force_recreate:
            return archive_path

        successful_certs = [c for c in certificates if c.status == CertificateStatus.SUCCESS and c.file_path]
        if not successful_certs:
            return None

        archive_path.parent.mkdir(parents=True, exist_ok=True)
        # Create temp zip first to prevent partial reads
        temp_archive_path = archive_path.with_suffix(".tmp")

        with zipfile.ZipFile(temp_archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            used_filenames: set[str] = set()

            for cert in successful_certs:
                if not cert.file_path:
                    continue
                file_path = Path(cert.file_path)
                if not file_path.exists():
                    continue

                safe_name = sanitize_filename(cert.recipient_name)
                arcname = f"{safe_name}_{cert.certificate_code}.pdf"

                # Prevent duplicate filename collisions
                counter = 1
                base_arcname = arcname
                while arcname in used_filenames:
                    arcname = f"{safe_name}_{cert.certificate_code}_{counter}.pdf"
                    counter += 1

                used_filenames.add(arcname)
                zip_file.write(file_path, arcname=arcname)

        if temp_archive_path.exists():
            temp_archive_path.replace(archive_path)
            return archive_path

        return None
