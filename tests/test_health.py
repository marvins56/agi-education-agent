"""Health endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def simple_client():
    """Minimal client that only needs the health router."""
    from fastapi import FastAPI
    from src.api.routers.health import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_health_endpoint(simple_client):
    response = await simple_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["service"] == "EduAGI"
