import asyncio
import pytest
from httpx import AsyncClient

from app.models.job import JobStatus


@pytest.mark.asyncio
async def test_verify_valid_certificate(client: AsyncClient):
    payload = {
        "title": "Security Verification Job",
        "event_name": "Cybersecurity & Cryptography",
        "organization": "National Security Institute",
        "recipients": [
            {"name": "Bruce Wayne", "email": "bruce@wayne-enterprises.com", "identifier": "BW-007"},
        ],
    }

    create_res = await client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    for _ in range(20):
        await asyncio.sleep(0.3)
        res = await client.get(f"/api/v1/jobs/{job_id}")
        if res.json()["status"] == JobStatus.COMPLETED.value:
            break

    job_data = (await client.get(f"/api/v1/jobs/{job_id}")).json()
    cert = job_data["certificates"][0]
    cert_code = cert["certificate_code"]

    # Verify certificate using its unique code
    verify_res = await client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["valid"] is True
    assert vdata["certificate_code"] == cert_code
    assert vdata["certificate_id"] == cert["id"]
    assert vdata["recipient_name"] == "Bruce Wayne"
    assert vdata["recipient_email"] == "bruce@wayne-enterprises.com"
    assert vdata["recipient_identifier"] == "BW-007"
    assert vdata["event_name"] == "Cybersecurity & Cryptography"
    assert vdata["organization"] == "National Security Institute"
    assert vdata["status"] == "SUCCESS"
    assert "authentic and valid" in vdata["message"].lower()


@pytest.mark.asyncio
async def test_verify_invalid_certificate_code(client: AsyncClient):
    verify_res = await client.get("/api/v1/certificates/verify/CERT-INVALID-CODE-9999")
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["valid"] is False
    assert vdata["certificate_code"] == "CERT-INVALID-CODE-9999"
    assert "not found" in vdata["message"].lower()
