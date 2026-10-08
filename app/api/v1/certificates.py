import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.certificate import CertificateStatus
from app.schemas.certificate import (
    CertificateResponse,
    CertificateVerificationResponse,
)
from app.services.job_service import JobService
from app.services.zip_service import sanitize_filename

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    response_model=CertificateResponse,
    summary="Get Certificate Details",
)
async def get_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
):
    cert = await JobService.get_certificate_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found",
        )

    return CertificateResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        recipient_identifier=cert.recipient_identifier,
        certificate_code=cert.certificate_code,
        status=cert.status,
        file_size_bytes=cert.file_size_bytes,
        error_message=cert.error_message,
        custom_data=cert.custom_data,
        created_at=cert.created_at,
        issued_at=cert.issued_at,
        download_url=f"/api/v1/certificates/{cert.id}/download" if cert.status == CertificateStatus.SUCCESS else None,
        verify_url=f"/api/v1/certificates/verify/{cert.certificate_code}",
    )


@router.get(
    "/{certificate_id}/download",
    summary="Download Individual Certificate PDF",
)
async def download_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
):
    cert = await JobService.get_certificate_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found",
        )

    if cert.status != CertificateStatus.SUCCESS or not cert.file_path:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not in SUCCESS state (current status: {cert.status.value}). Reason: {cert.error_message or 'Still processing or failed'}",
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file not found on disk.",
        )

    safe_name = sanitize_filename(cert.recipient_name)
    filename = f"Certificate_{safe_name}_{cert.certificate_code}.pdf"

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get(
    "/verify/{certificate_code}",
    response_model=CertificateVerificationResponse,
    summary="Verify Certificate Authenticity",
    description="Public endpoint to verify the validity and authenticity of a certificate using its unique certificate code.",
)
async def verify_certificate(
    certificate_code: str,
    db: AsyncSession = Depends(get_db),
):
    return await JobService.verify_certificate_code(db, certificate_code.strip())
