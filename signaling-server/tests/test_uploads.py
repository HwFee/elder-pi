import io
import pytest
from httpx import AsyncClient, ASGITransport

from app.config import get_settings
from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "avatars"))
    get_settings.cache_clear()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_upload_avatar(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": r.json()["owner_id"], "display_name": "Self", "button_index": 1
    }, headers=headers)
    contact_id = r.json()["id"]

    avatar = io.BytesIO(b"fake-image-bytes")
    r = await client.post(f"/api/contacts/{contact_id}/avatar", files={"file": ("avatar.png", avatar, "image/png")}, headers=headers)
    assert r.status_code == 200
    assert r.json()["avatar_path"] is not None
