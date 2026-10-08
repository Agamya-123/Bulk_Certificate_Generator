import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_empty_recipients_list_rejected(client: AsyncClient):
    payload = {
        "title": "Empty Recipients Test",
        "event_name": "Testing Course",
        "recipients": [],
    }
    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
    errors = response.json().get("detail", [])
    assert any("recipients" in str(err) for err in errors)


@pytest.mark.asyncio
async def test_invalid_email_format_rejected(client: AsyncClient):
    payload = {
        "title": "Invalid Email Test",
        "event_name": "Testing Course",
        "recipients": [
            {"name": "Valid User", "email": "not-a-valid-email"},
        ],
    }
    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any("email" in str(err).lower() for err in errors)


@pytest.mark.asyncio
async def test_blank_recipient_name_rejected(client: AsyncClient):
    payload = {
        "title": "Blank Name Test",
        "event_name": "Testing Course",
        "recipients": [
            {"name": "   ", "email": "valid@example.com"},
        ],
    }
    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any("name" in str(err).lower() for err in errors)


@pytest.mark.asyncio
async def test_missing_required_fields_rejected(client: AsyncClient):
    payload = {
        "title": "Missing Event Name",
        # "event_name" is missing
        "recipients": [{"name": "User One", "email": "user@example.com"}],
    }
    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_default_values_applied_when_omitted(client: AsyncClient):
    payload = {
        "title": "Defaults Verification Job",
        "event_name": "Automation Testing 101",
        "recipients": [
            {"name": "Grace Hopper", "email": "grace@example.com"},
        ],
    }
    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_res = await client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    # Verify defaults are set
    assert job_data["issuer_name"] != ""
    assert job_data["issuer_title"] != ""
    assert job_data["organization"] != ""
    assert job_data["issue_date"] != ""
    assert job_data["template_name"] == "classic_gold"
