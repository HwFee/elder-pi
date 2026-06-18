import pytest
from httpx import AsyncClient, ASGITransport

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_get_device(client, auth_headers):
    r = await client.post("/api/devices", json={"display_name": "Grandma Pi"}, headers=auth_headers)
    assert r.status_code == 201
    device_id = r.json()["device_id"]

    r = await client.get(f"/api/devices/{device_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["display_name"] == "Grandma Pi"
