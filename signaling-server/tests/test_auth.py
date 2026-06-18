import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db import async_engine, Base


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


async def test_register_and_login(client):
    payload = {"email": "alice@example.com", "password": "secret", "full_name": "Alice"}
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 201
    assert r.json()["email"] == "alice@example.com"

    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_login_invalid_password(client):
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "wrong"})
    assert r.status_code == 401
