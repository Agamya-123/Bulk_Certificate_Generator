import asyncio
import pytest
from httpx import AsyncClient

from app.models.job import JobStatus


@pytest.mark.asyncio
async def test_job_processing_lifecycle_and_progress(client: AsyncClient):
    # Submit job with 4 recipients
    recipients = [
        {"name": f"Candidate {i}", "email": f"candidate{i}@example.com", "identifier": f"ID-{i}"}
        for i in range(1, 5)
    ]
    payload = {
        "title": "Machine Learning Masterclass",
        "event_name": "Deep Learning & Transformers",
        "recipients": recipients,
    }

    create_res = await client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["job_id"]
    assert create_res.json()["total_recipients"] == 4

    # Wait / poll until background processing finishes (or up to 10 seconds)
    max_retries = 20
    final_data = None
    for _ in range(max_retries):
        await asyncio.sleep(0.3)
        status_res = await client.get(f"/api/v1/jobs/{job_id}")
        assert status_res.status_code == 200
        data = status_res.json()
        if data["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.PARTIALLY_COMPLETED.value]:
            final_data = data
            break

    assert final_data is not None, "Job did not complete within timeout"
    assert final_data["status"] == JobStatus.COMPLETED.value
    assert final_data["total_count"] == 4
    assert final_data["processed_count"] == 4
    assert final_data["success_count"] == 4
    assert final_data["failed_count"] == 0
    assert final_data["progress_percentage"] == 100.0
    assert final_data["completed_at"] is not None
    assert len(final_data["certificates"]) == 4

    for cert in final_data["certificates"]:
        assert cert["status"] == "SUCCESS"
        assert cert["download_url"] is not None
        assert cert["file_size_bytes"] > 0
        assert cert["error_message"] is None
