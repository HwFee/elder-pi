import io
import pytest
from httpx import AsyncClient, ASGITransport

from app.config import get_settings
from app.db import async_engine, Base
from app.main import app


VALID_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452"
    "000000010000000108060000001f15c4"
    "890000000a49444154789c6300010000"
    "0500010d0a2db40000000049454e44ae"
    "426082"
)


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
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.get("/api/auth/me", headers=headers)
    user_id = r.json()["id"]

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": user_id, "display_name": "Self", "button_index": 1
    }, headers=headers)
    contact_id = r.json()["id"]

    avatar = io.BytesIO(VALID_PNG)
    r = await client.post(f"/api/contacts/{contact_id}/avatar", files={"file": ("avatar.png", avatar, "image/png")}, headers=headers)
    assert r.status_code == 200
    assert r.json()["avatar_path"] is not None

    avatar_path = r.json()["avatar_path"]
    r = await client.get(f"/uploads/{avatar_path}", headers=headers)
    assert r.status_code == 200


async def test_upload_avatar_rejects_non_image(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.get("/api/auth/me", headers=headers)
    user_id = r.json()["id"]

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": user_id, "display_name": "Self", "button_index": 1
    }, headers=headers)
    contact_id = r.json()["id"]

    fake = io.BytesIO(b"not-an-image")
    r = await client.post(
        f"/api/contacts/{contact_id}/avatar",
        files={"file": ("avatar.png", fake, "image/png")},
        headers=headers,
    )
    assert r.status_code == 400
