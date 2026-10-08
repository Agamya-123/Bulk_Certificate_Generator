from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.certificate import CertificateStatus


class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Recipient's full legal or preferred name")
    email: EmailStr = Field(..., description="Recipient's valid email address")
    identifier: Optional[str] = Field(None, max_length=100, description="Optional unique identifier (e.g. Student ID, Roll No)")
    custom_data: Optional[dict[str, Any]] = Field(default=None, description="Optional custom key-value attributes (e.g. grade, honors)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Recipient name cannot be blank or whitespace only")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    recipient_identifier: Optional[str] = None
    certificate_code: str
    status: CertificateStatus
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    custom_data: Optional[dict[str, Any]] = None
    created_at: datetime
    issued_at: Optional[datetime] = None
    download_url: Optional[str] = None
    verify_url: Optional[str] = None


class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_code: str
    certificate_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_identifier: Optional[str] = None
    event_name: Optional[str] = None
    issue_date: Optional[str] = None
    organization: Optional[str] = None
    issuer_name: Optional[str] = None
    issuer_title: Optional[str] = None
    issued_at: Optional[datetime] = None
    status: CertificateStatus
    message: str
