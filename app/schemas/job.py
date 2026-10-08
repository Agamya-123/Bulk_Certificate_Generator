from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import settings
from app.models.job import JobStatus
from app.schemas.certificate import CertificateResponse, RecipientInput


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Human-readable title for this generation batch")
    event_name: str = Field(..., min_length=2, max_length=255, description="Name of the course, workshop, event, or program")
    issue_date: Optional[str] = Field(None, max_length=50, description="Date printed on certificate. Defaults to today's date if omitted.")
    issuer_name: Optional[str] = Field(None, max_length=255, description="Name of signatory / authority")
    issuer_title: Optional[str] = Field(None, max_length=255, description="Title of signatory (e.g. Program Director)")
    organization: Optional[str] = Field(None, max_length=255, description="Issuing organization or institution")
    description: Optional[str] = Field(None, description="Optional internal notes or job description")
    template_name: Optional[str] = Field("classic_gold", max_length=100, description="Template identifier for certificate styling")
    recipients: list[RecipientInput] = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_RECIPIENTS_PER_JOB,
        description="List of recipients to generate certificates for",
    )

    @field_validator("title", "event_name")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank")
        return cleaned

    @field_validator("issue_date")
    @classmethod
    def default_issue_date(cls, v: Optional[str]) -> str:
        if v and v.strip():
            return v.strip()
        return datetime.now(timezone.utc).strftime("%B %d, %Y")

    @field_validator("issuer_name")
    @classmethod
    def default_issuer_name(cls, v: Optional[str]) -> str:
        if v and v.strip():
            return v.strip()
        return settings.DEFAULT_ISSUER_NAME

    @field_validator("issuer_title")
    @classmethod
    def default_issuer_title(cls, v: Optional[str]) -> str:
        if v and v.strip():
            return v.strip()
        return settings.DEFAULT_ISSUER_TITLE

    @field_validator("organization")
    @classmethod
    def default_organization(cls, v: Optional[str]) -> str:
        if v and v.strip():
            return v.strip()
        return settings.DEFAULT_ORGANIZATION


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    event_name: str
    issue_date: str
    issuer_name: str
    issuer_title: str
    organization: str
    description: Optional[str] = None
    template_name: str
    status: JobStatus
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    download_zip_url: Optional[str] = None


class JobDetailResponse(JobSummaryResponse):
    certificates: list[CertificateResponse] = []


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    total_recipients: int
    message: str
    status_url: str
    download_zip_url: Optional[str] = None
