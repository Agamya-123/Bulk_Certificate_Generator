import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_create_generation_job(client: AsyncClient):
    payload = {
        "title": "Full-Stack Web Development Bootcamp",
        "event_name": "Full-Stack Web Development Mastery",
        "issue_date": "October 8, 2026",
        "issuer_name": "Dr. Sarah Connor",
        "issuer_title": "Head of Engineering",
        "organization": "Tech Excellence Institute",
        "recipients": [
            {
                "name": "Alice Wonderland",
                "email": "alice@example.com",
                "identifier": "STU-001",
                "custom_data": {"grade": "Distinction", "track": "Frontend"},
            },
            {
                "name": "Bob Builder",
                "email": "bob@example.com",
                "identifier": "STU-002",
                "custom_data": {"grade": "Merit", "track": "Backend"},
            },
            {
                "name": "Charlie Brown",
                "email": "charlie@example.com",
                "identifier": "STU-003",
            },
        ],
    }

    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_recipients"] == 3
    assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]
    assert "/api/v1/jobs/" in data["status_url"]


@pytest.mark.asyncio
async def test_list_jobs(client: AsyncClient):
    # Create two jobs
    for i in range(2):
        await client.post(
            "/api/v1/jobs",
            json={
                "title": f"Workshop Batch {i}",
                "event_name": "Cloud Architecture",
                "recipients": [{"name": f"User {i}", "email": f"user{i}@example.com"}],
            },
        )

    response = await client.get("/api/v1/jobs?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert data["page"] == 1

    # Search filter
    search_res = await client.get("/api/v1/jobs?search=Batch%200")
    assert search_res.status_code == 200
    sdata = search_res.json()
    assert sdata["total"] >= 1
    assert any("Batch 0" in item["title"] for item in sdata["items"])


@pytest.mark.asyncio
async def test_list_job_certificates_endpoint(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Certificates List Test Job",
            "event_name": "Testing Course",
            "recipients": [
                {"name": "Alice Wonderland", "email": "alice@example.com"},
                {"name": "Bob Builder", "email": "bob@example.com"},
            ],
        },
    )
    job_id = create_res.json()["job_id"]

    # List certificates
    res = await client.get(f"/api/v1/jobs/{job_id}/certificates?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Not found case
    res_404 = await client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000/certificates")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_get_job_status_not_found(client: AsyncClient):
    response = await client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_job(client: AsyncClient):
    # Create job
    create_res = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Job to Delete",
            "event_name": "Event Delete Test",
            "recipients": [{"name": "David Bowie", "email": "david@example.com"}],
        },
    )
    job_id = create_res.json()["job_id"]

    # Delete job
    del_res = await client.delete(f"/api/v1/jobs/{job_id}")
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # Confirm 404 after deletion
    get_res = await client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 404
