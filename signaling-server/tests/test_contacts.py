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
async def alice(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    return r.json()["access_token"]


@pytest.fixture
async def bob(client):
    await client.post("/api/auth/register", json={
        "email": "bob@example.com", "password": "secret", "full_name": "Bob"
    })
    r = await client.post("/api/auth/login", data={"username": "bob@example.com", "password": "secret"})
    token = r.json()["access_token"]
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"id": r.json()["id"], "token": token}


async def test_create_contact_requires_unique_button_index(client, alice, bob):
    headers = {"Authorization": f"Bearer {alice}"}
    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": bob["id"], "display_name": "Bob", "button_index": 1
    }, headers=headers)
    assert r.status_code == 201

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": bob["id"], "display_name": "Bob 2", "button_index": 1
    }, headers=headers)
    assert r.status_code == 400


async def test_update_contact_rejects_duplicate_button_index(client, alice, bob):
    headers = {"Authorization": f"Bearer {alice}"}
    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": bob["id"], "display_name": "Bob", "button_index": 1
    }, headers=headers)
    assert r.status_code == 201
    contact_id = r.json()["id"]

    await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": bob["id"], "display_name": "Bob 2", "button_index": 2
    }, headers=headers)

    r = await client.patch(
        f"/api/contacts/{contact_id}",
        json={"button_index": 2},
        headers=headers,
    )
    assert r.status_code == 409
