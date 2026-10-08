import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.certificate import Certificate, CertificateStatus
from app.models.job import Job, JobStatus
from app.services.generator import CertificateData, CertificateGenerator
from app.services.zip_service import ZipService
from app.utils.file_manager import get_certificate_path, get_file_size_safely

logger = logging.getLogger(__name__)

# Global thread pool for PDF generation tasks
_thread_pool = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)


def _generate_single_pdf_worker(
    recipient_name: str,
    recipient_email: str,
    recipient_identifier: Optional[str],
    custom_data: Optional[dict],
    event_name: str,
    issue_date: str,
    issuer_name: str,
    issuer_title: str,
    organization: str,
    certificate_code: str,
    output_path: Path,
    base_url: str,
) -> tuple[bool, Optional[str], Optional[int]]:
    """
    Synchronous worker function that generates a single certificate PDF.
    Executed inside thread pool.
    Returns: (success: bool, error_message: Optional[str], file_size: Optional[int])
    """
    try:
        verification_url = f"{base_url}/api/v1/certificates/verify/{certificate_code}"
        data = CertificateData(
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            event_name=event_name,
            issue_date=issue_date,
            issuer_name=issuer_name,
            issuer_title=issuer_title,
            organization=organization,
            certificate_code=certificate_code,
            recipient_identifier=recipient_identifier,
            custom_data=custom_data,
            verification_url=verification_url,
        )
        CertificateGenerator.generate_pdf(data, output_path)
        size = get_file_size_safely(str(output_path))
        return True, None, size
    except Exception as e:
        logger.error(
            "Failed to generate certificate for %s (%s): %s",
            recipient_name,
            recipient_email,
            str(e),
            exc_info=True,
        )
        return False, f"Generation error: {str(e)}", None


class BulkJobProcessor:
    """Orchestrates bulk certificate generation with background execution and fault tolerance."""

    @classmethod
    async def process_job(cls, job_id: str) -> None:
        """
        Background task entry point to process all certificates for a job.
        Uses its own database session.
        """
        logger.info("Starting background processing for Job ID: %s", job_id)
        async with AsyncSessionLocal() as session:
            try:
                # 1. Fetch Job
                stmt = select(Job).where(Job.id == job_id)
                result = await session.execute(stmt)
                job = result.scalar_one_or_none()

                if not job:
                    logger.error("Job %s not found for processing", job_id)
                    return

                job.status = JobStatus.PROCESSING
                job.updated_at = datetime.now(timezone.utc)
                await session.commit()

                # 2. Fetch all certificates for this job
                cert_stmt = (
                    select(Certificate)
                    .where(Certificate.job_id == job_id)
                    .order_by(Certificate.created_at)
                )
                cert_res = await session.execute(cert_stmt)
                certificates = list(cert_res.scalars().all())

                if not certificates:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return

                loop = asyncio.get_running_loop()

                # 3. Process certificates concurrently in batches
                batch_size = 50
                processed = 0
                success_count = 0
                failed_count = 0

                for i in range(0, len(certificates), batch_size):
                    chunk = certificates[i : i + batch_size]
                    tasks = []

                    for cert in chunk:
                        output_path = get_certificate_path(job.id, cert.id, extension="pdf")
                        tasks.append(
                            loop.run_in_executor(
                                _thread_pool,
                                _generate_single_pdf_worker,
                                cert.recipient_name,
                                cert.recipient_email,
                                cert.recipient_identifier,
                                cert.custom_data,
                                job.event_name,
                                job.issue_date,
                                job.issuer_name,
                                job.issuer_title,
                                job.organization,
                                cert.certificate_code,
                                output_path,
                                settings.BASE_URL,
                            )
                        )

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for cert, res in zip(chunk, results):
                        processed += 1
                        if isinstance(res, Exception):
                            cert.status = CertificateStatus.FAILED
                            cert.error_message = f"Unexpected worker error: {str(res)}"
                            failed_count += 1
                        else:
                            success, err_msg, file_size = res
                            if success:
                                cert.status = CertificateStatus.SUCCESS
                                cert.file_path = str(get_certificate_path(job.id, cert.id, "pdf"))
                                cert.file_size_bytes = file_size
                                cert.issued_at = datetime.now(timezone.utc)
                                cert.error_message = None
                                success_count += 1
                            else:
                                cert.status = CertificateStatus.FAILED
                                cert.error_message = err_msg or "Unknown generation error"
                                failed_count += 1

                    # Update job progress in database
                    job.processed_count = processed
                    job.success_count = success_count
                    job.failed_count = failed_count
                    job.updated_at = datetime.now(timezone.utc)
                    await session.commit()

                # 4. Finalize Job Status
                now = datetime.now(timezone.utc)
                job.completed_at = now
                job.updated_at = now

                if success_count == len(certificates):
                    job.status = JobStatus.COMPLETED
                elif success_count > 0:
                    job.status = JobStatus.PARTIALLY_COMPLETED
                else:
                    job.status = JobStatus.FAILED

                # 5. Create bulk ZIP archive if there are successful certificates
                if success_count > 0:
                    try:
                        archive_path = await loop.run_in_executor(
                            _thread_pool,
                            ZipService.create_job_archive,
                            job.id,
                            certificates,
                            True,
                        )
                        if archive_path:
                            job.archive_path = str(archive_path)
                    except Exception as zip_err:
                        logger.warning("Failed to create ZIP archive for job %s: %s", job_id, str(zip_err))

                await session.commit()
                logger.info(
                    "Completed Job %s. Success: %d, Failed: %d, Total: %d, Status: %s",
                    job_id,
                    success_count,
                    failed_count,
                    len(certificates),
                    job.status.value,
                )

            except Exception as e:
                logger.critical("Fatal error processing job %s: %s", job_id, str(e), exc_info=True)
                # Ensure job is marked as failed if unexpected fatal error
                try:
                    stmt = select(Job).where(Job.id == job_id)
                    result = await session.execute(stmt)
                    job = result.scalar_one_or_none()
                    if job:
                        job.status = JobStatus.FAILED
                        job.updated_at = datetime.now(timezone.utc)
                        job.completed_at = datetime.now(timezone.utc)
                        await session.commit()
                except Exception:
                    pass
