import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_app(client: AsyncClient):
    response = await client.get("/")
    print("[Response]:", response.json())
    assert response.status_code == 200
