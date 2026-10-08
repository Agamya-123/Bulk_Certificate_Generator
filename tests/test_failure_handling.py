import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.job import JobStatus
from app.services.generator import CertificateData, CertificateGenerator


@pytest.mark.asyncio
async def test_single_certificate_failure_does_not_abort_batch(client: AsyncClient):
    """
    Test that when one certificate fails during rendering, the rest of the batch
    succeeds, the job status reflects PARTIALLY_COMPLETED, and the failed item has error details.
    """
    orig_generate_pdf = CertificateGenerator.generate_pdf

    def faulty_generate_pdf(data: CertificateData, output_path: Path) -> Path:
        if "BadRecipient" in data.recipient_name:
            raise RuntimeError("Simulated rendering/font corruption error for BadRecipient")
        return orig_generate_pdf(data, output_path)

    recipients = [
        {"name": "Good Recipient One", "email": "good1@example.com"},
        {"name": "BadRecipient Fails", "email": "bad@example.com"},
        {"name": "Good Recipient Two", "email": "good2@example.com"},
    ]
    payload = {
        "title": "Resilience Test Workshop",
        "event_name": "Robust System Design",
        "recipients": recipients,
    }

    with patch.object(CertificateGenerator, "generate_pdf", side_effect=faulty_generate_pdf):
        create_res = await client.post("/api/v1/jobs", json=payload)
        assert create_res.status_code == 202
        job_id = create_res.json()["job_id"]

        # Poll until finished
        final_data = None
        for _ in range(20):
            await asyncio.sleep(0.3)
            status_res = await client.get(f"/api/v1/jobs/{job_id}")
            data = status_res.json()
            if data["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.PARTIALLY_COMPLETED.value]:
                final_data = data
                break

    assert final_data is not None
    assert final_data["status"] == JobStatus.PARTIALLY_COMPLETED.value
    assert final_data["total_count"] == 3
    assert final_data["processed_count"] == 3
    assert final_data["success_count"] == 2
    assert final_data["failed_count"] == 1

    # Check individual certificate details
    certs = final_data["certificates"]
    assert len(certs) == 3

    failed_certs = [c for c in certs if c["status"] == "FAILED"]
    success_certs = [c for c in certs if c["status"] == "SUCCESS"]

    assert len(failed_certs) == 1
    assert "BadRecipient" in failed_certs[0]["recipient_name"]
    assert "Simulated rendering/font corruption error" in failed_certs[0]["error_message"]
    assert failed_certs[0]["download_url"] is None

    assert len(success_certs) == 2
    for sc in success_certs:
        assert sc["download_url"] is not None
        assert sc["file_size_bytes"] > 0


@pytest.mark.asyncio
async def test_all_certificates_failing_sets_job_failed(client: AsyncClient):
    """Test that when all certificates fail, the job status is FAILED."""
    def fail_all(data: CertificateData, output_path: Path) -> Path:
        raise RuntimeError("Global generation failure")

    recipients = [
        {"name": "Recipient A", "email": "a@example.com"},
        {"name": "Recipient B", "email": "b@example.com"},
    ]
    payload = {
        "title": "All Fail Test",
        "event_name": "Test Event",
        "recipients": recipients,
    }

    with patch.object(CertificateGenerator, "generate_pdf", side_effect=fail_all):
        create_res = await client.post("/api/v1/jobs", json=payload)
        job_id = create_res.json()["job_id"]

        final_data = None
        for _ in range(20):
            await asyncio.sleep(0.3)
            status_res = await client.get(f"/api/v1/jobs/{job_id}")
            data = status_res.json()
            if data["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.PARTIALLY_COMPLETED.value]:
                final_data = data
                break

    assert final_data is not None
    assert final_data["status"] == JobStatus.FAILED.value
    assert final_data["success_count"] == 0
    assert final_data["failed_count"] == 2
