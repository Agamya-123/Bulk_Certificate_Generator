import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.certificate import Certificate, CertificateStatus
from app.models.job import Job, JobStatus
from app.schemas.certificate import (
    CertificateResponse,
    CertificateVerificationResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.job import (
    JobCreateRequest,
    JobDetailResponse,
    JobSummaryResponse,
)
from app.utils.file_manager import delete_job_files
from app.utils.security import generate_certificate_code


class JobService:

    @classmethod
    async def create_job(cls, db: AsyncSession, request: JobCreateRequest) -> Job:
        """
        Create a new certificate generation job and all its pending certificate records
        within a single transaction.
        """
        job = Job(
            title=request.title,
            event_name=request.event_name,
            issue_date=request.issue_date or datetime.now(timezone.utc).strftime("%B %d, %Y"),
            issuer_name=request.issuer_name or settings.DEFAULT_ISSUER_NAME,
            issuer_title=request.issuer_title or settings.DEFAULT_ISSUER_TITLE,
            organization=request.organization or settings.DEFAULT_ORGANIZATION,
            description=request.description,
            template_name=request.template_name or "classic_gold",
            status=JobStatus.PENDING,
            total_count=len(request.recipients),
            processed_count=0,
            success_count=0,
            failed_count=0,
        )
        db.add(job)
        await db.flush()  # Generates job.id

        # Create certificate records
        certificates: list[Certificate] = []
        for recipient in request.recipients:
            cert_code = generate_certificate_code()
            cert = Certificate(
                job_id=job.id,
                recipient_name=recipient.name,
                recipient_email=recipient.email,
                recipient_identifier=recipient.identifier,
                certificate_code=cert_code,
                status=CertificateStatus.PENDING,
                custom_data=recipient.custom_data,
            )
            certificates.append(cert)

        db.add_all(certificates)
        await db.commit()
        await db.refresh(job)
        return job

    @classmethod
    async def get_job_by_id(cls, db: AsyncSession, job_id: str) -> Optional[Job]:
        """Fetch a job by ID with its certificates."""
        stmt = (
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.certificates))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_jobs(
        cls,
        db: AsyncSession,
        status: Optional[JobStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[JobSummaryResponse]:
        """List jobs with filtering and pagination."""
        stmt = select(Job)

        if status:
            stmt = stmt.where(Job.status == status)
        if search:
            search_filter = f"%{search}%"
            stmt = stmt.where(
                (Job.title.ilike(search_filter))
                | (Job.event_name.ilike(search_filter))
                | (Job.organization.ilike(search_filter))
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Pagination & ordering
        stmt = (
            stmt.order_by(Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        jobs = result.scalars().all()

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        items = [
            JobSummaryResponse(
                id=j.id,
                title=j.title,
                event_name=j.event_name,
                issue_date=j.issue_date,
                issuer_name=j.issuer_name,
                issuer_title=j.issuer_title,
                organization=j.organization,
                description=j.description,
                template_name=j.template_name,
                status=j.status,
                total_count=j.total_count,
                processed_count=j.processed_count,
                success_count=j.success_count,
                failed_count=j.failed_count,
                progress_percentage=j.progress_percentage,
                created_at=j.created_at,
                updated_at=j.updated_at,
                completed_at=j.completed_at,
                download_zip_url=f"/api/v1/jobs/{j.id}/download-zip" if j.success_count > 0 else None,
            )
            for j in jobs
        ]

        return PaginatedResponse(
            items=items,
            total=total_count,
            page=page,
            page_size=page_size,
            pages=total_pages,
        )

    @classmethod
    async def list_job_certificates(
        cls,
        db: AsyncSession,
        job_id: str,
        status: Optional[CertificateStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[CertificateResponse]:
        """List certificates belonging to a job with optional status filter."""
        stmt = select(Certificate).where(Certificate.job_id == job_id)

        if status:
            stmt = stmt.where(Certificate.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            stmt.order_by(Certificate.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        certificates = result.scalars().all()

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        items = [
            CertificateResponse(
                id=c.id,
                job_id=c.job_id,
                recipient_name=c.recipient_name,
                recipient_email=c.recipient_email,
                recipient_identifier=c.recipient_identifier,
                certificate_code=c.certificate_code,
                status=c.status,
                file_size_bytes=c.file_size_bytes,
                error_message=c.error_message,
                custom_data=c.custom_data,
                created_at=c.created_at,
                issued_at=c.issued_at,
                download_url=f"/api/v1/certificates/{c.id}/download" if c.status == CertificateStatus.SUCCESS else None,
                verify_url=f"/api/v1/certificates/verify/{c.certificate_code}",
            )
            for c in certificates
        ]

        return PaginatedResponse(
            items=items,
            total=total_count,
            page=page,
            page_size=page_size,
            pages=total_pages,
        )

    @classmethod
    async def get_certificate_by_id(cls, db: AsyncSession, certificate_id: str) -> Optional[Certificate]:
        """Fetch a single certificate by primary key."""
        stmt = select(Certificate).where(Certificate.id == certificate_id).options(selectinload(Certificate.job))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def verify_certificate_code(cls, db: AsyncSession, certificate_code: str) -> CertificateVerificationResponse:
        """Verify the validity of a certificate using its unique code."""
        stmt = (
            select(Certificate)
            .where(Certificate.certificate_code == certificate_code)
            .options(selectinload(Certificate.job))
        )
        result = await db.execute(stmt)
        cert = result.scalar_one_or_none()

        if not cert:
            return CertificateVerificationResponse(
                valid=False,
                certificate_code=certificate_code,
                status=CertificateStatus.FAILED,
                message="Certificate code not found. The code may be invalid or not yet issued.",
            )

        if cert.status != CertificateStatus.SUCCESS:
            return CertificateVerificationResponse(
                valid=False,
                certificate_code=certificate_code,
                status=cert.status,
                message=f"Certificate exists but has status {cert.status.value}. Not a valid issued certificate.",
            )

        job = cert.job
        return CertificateVerificationResponse(
            valid=True,
            certificate_code=cert.certificate_code,
            certificate_id=cert.id,
            recipient_name=cert.recipient_name,
            recipient_email=cert.recipient_email,
            recipient_identifier=cert.recipient_identifier,
            event_name=job.event_name if job else None,
            issue_date=job.issue_date if job else None,
            organization=job.organization if job else None,
            issuer_name=job.issuer_name if job else None,
            issuer_title=job.issuer_title if job else None,
            issued_at=cert.issued_at,
            status=cert.status,
            message="Certificate is authentic and valid.",
        )

    @classmethod
    async def delete_job(cls, db: AsyncSession, job_id: str) -> bool:
        """Delete a job, its database records, and all associated files."""
        job = await cls.get_job_by_id(db, job_id)
        if not job:
            return False

        # Remove files
        delete_job_files(job_id)

        # Delete from DB
        await db.delete(job)
        await db.commit()
        return True
