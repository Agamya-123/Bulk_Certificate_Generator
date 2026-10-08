import asyncio
import io
import zipfile

import pytest
from httpx import AsyncClient

from app.models.job import JobStatus


@pytest.mark.asyncio
async def test_retrieve_individual_certificate_and_download(client: AsyncClient):
    payload = {
        "title": "Retrieval Test Job",
        "event_name": "API Design Masterclass",
        "recipients": [
            {"name": "Grace Hopper", "email": "grace@navy.mil", "identifier": "GH-1906"},
        ],
    }

    create_res = await client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # Wait for completion
    for _ in range(20):
        await asyncio.sleep(0.3)
        res = await client.get(f"/api/v1/jobs/{job_id}")
        if res.json()["status"] == JobStatus.COMPLETED.value:
            break

    job_data = (await client.get(f"/api/v1/jobs/{job_id}")).json()
    cert = job_data["certificates"][0]
    cert_id = cert["id"]

    # 1. Test get certificate details
    detail_res = await client.get(f"/api/v1/certificates/{cert_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["recipient_name"] == "Grace Hopper"
    assert detail_res.json()["status"] == "SUCCESS"

    # 2. Test download single certificate PDF
    download_res = await client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert download_res.content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_retrieve_bulk_zip_archive(client: AsyncClient):
    payload = {
        "title": "Bulk Archive Test Job",
        "event_name": "Python Distributed Systems",
        "recipients": [
            {"name": "User Alpha", "email": "alpha@example.com"},
            {"name": "User Beta", "email": "beta@example.com"},
            {"name": "User Gamma", "email": "gamma@example.com"},
        ],
    }

    create_res = await client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # Wait for completion
    for _ in range(20):
        await asyncio.sleep(0.3)
        res = await client.get(f"/api/v1/jobs/{job_id}")
        if res.json()["status"] == JobStatus.COMPLETED.value:
            break

    # Download bulk zip
    zip_res = await client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Verify contents of zip file
    zip_buffer = io.BytesIO(zip_res.content)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        file_list = zf.namelist()
        assert len(file_list) == 3
        for fname in file_list:
            assert fname.endswith(".pdf")
            # Verify file inside is valid PDF
            content = zf.read(fname)
            assert content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_download_nonexistent_certificate_returns_404(client: AsyncClient):
    res = await client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_certificate_details_returns_404(client: AsyncClient):
    res = await client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_download_zip_for_nonexistent_job_returns_404(client: AsyncClient):
    res = await client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000/download-zip")
    assert res.status_code == 404
