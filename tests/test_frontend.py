import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_frontend_spa_root(client: AsyncClient):
    """Test that GET / serves the SPA index.html."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Bulk Certificate Generator" in response.text
    assert "nav-tab-generator" in response.text
    assert "nav-tab-monitor" in response.text


@pytest.mark.asyncio
async def test_static_assets_serving(client: AsyncClient):
    """Test that static CSS and JS files are served correctly."""
    # Test CSS
    css_res = await client.get("/static/css/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers.get("content-type", "") or "text/plain" in css_res.headers.get("content-type", "")

    # Test JS app entrypoint
    js_res = await client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers.get("content-type", "") or "text/plain" in js_res.headers.get("content-type", "")
