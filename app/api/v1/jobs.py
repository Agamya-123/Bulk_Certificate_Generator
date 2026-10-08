from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.certificate import CertificateStatus
from app.models.job import JobStatus
from app.schemas.certificate import CertificateResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.job import (
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
)
from app.services.job_service import JobService
from app.services.processor import BulkJobProcessor
from app.services.zip_service import ZipService
from app.utils.file_manager import get_job_archive_path

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Create Bulk Certificate Generation Job",
    description="Accepts a list of recipients and certificate details, queues the generation process, and returns a tracking ID.",
)
async def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # 1. Validate and store job + recipient records atomically
    job = await JobService.create_job(db, request)

    # 2. Queue background task for non-blocking asynchronous certificate generation
    background_tasks.add_task(BulkJobProcessor.process_job, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_count,
        message=f"Generation job accepted for {job.total_count} recipients. Processing started in background.",
        status_url=f"/api/v1/jobs/{job.id}",
        download_zip_url=f"/api/v1/jobs/{job.id}/download-zip",
    )


@router.get(
    "",
    response_model=PaginatedResponse[JobSummaryResponse],
    summary="List All Generation Jobs",
)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    search: Optional[str] = Query(None, description="Search in title, event name, or organization"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    return await JobService.list_jobs(
        db=db,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get Job Status & Progress",
    description="Retrieve real-time status, counters, progress percentage, and list of generated certificates with individual statuses and error details.",
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    job = await JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    cert_responses = [
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
        for c in job.certificates
    ]

    return JobDetailResponse(
        id=job.id,
        title=job.title,
        event_name=job.event_name,
        issue_date=job.issue_date,
        issuer_name=job.issuer_name,
        issuer_title=job.issuer_title,
        organization=job.organization,
        description=job.description,
        template_name=job.template_name,
        status=job.status,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress_percentage=job.progress_percentage,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        download_zip_url=f"/api/v1/jobs/{job.id}/download-zip" if job.success_count > 0 else None,
        certificates=cert_responses,
    )


@router.get(
    "/{job_id}/certificates",
    response_model=PaginatedResponse[CertificateResponse],
    summary="List Certificates in a Job",
)
async def list_job_certificates(
    job_id: str,
    status: Optional[CertificateStatus] = Query(None, description="Filter certificates by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    job = await JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    return await JobService.list_job_certificates(
        db=db,
        job_id=job_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}/download-zip",
    summary="Download All Certificates (Bulk ZIP)",
    description="Downloads a ZIP archive containing all successfully generated certificates for this job.",
)
async def download_job_zip(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    job = await JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    if job.status == JobStatus.PENDING:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Job is still pending processing. Please wait for certificates to be generated.",
        )

    if job.success_count == 0:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No certificates were successfully generated for this job.",
        )

    archive_path = get_job_archive_path(job_id)
    if not archive_path.exists():
        # Build archive if not already built or cached
        created_path = ZipService.create_job_archive(job.id, job.certificates, force_recreate=True)
        if not created_path or not created_path.exists():
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to package certificates into a ZIP archive.",
            )
        archive_path = created_path

    safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in job.title)
    filename = f"Certificates_{safe_title}_{job_id[:8]}.zip"

    return FileResponse(
        path=str(archive_path),
        media_type="application/zip",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/{job_id}",
    response_model=MessageResponse,
    summary="Delete Job & Associated Certificates",
    description="Deletes the job, all certificate database records, and all generated PDF and archive files.",
)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    deleted = await JobService.delete_job(db, job_id)
    if not deleted:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    return MessageResponse(message=f"Job '{job_id}' and all associated files deleted successfully.")
