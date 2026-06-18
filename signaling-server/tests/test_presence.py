from datetime import datetime, timedelta

import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.socket.manager import ConnectionManager
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


def test_manager_tracks_online_status():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    assert mgr.is_online("device-1") is True
    mgr.disconnect("sid-1")
    assert mgr.is_online("device-1") is False


def test_heartbeat_updates_last_seen():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    old = mgr.get_last_seen("device-1")
    time.sleep(0.01)
    mgr.heartbeat("device-1")
    new = mgr.get_last_seen("device-1")
    assert new > old


def test_sweep_stale_marks_offline():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    mgr._last_seen["device-1"] = datetime.utcnow() - timedelta(seconds=120)
    mgr.sweep_stale(timeout_seconds=60)
    assert mgr.is_online("device-1") is False


def test_disconnect_after_sweep_is_safe():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    mgr._last_seen["device-1"] = datetime.utcnow() - timedelta(seconds=120)
    mgr.sweep_stale(timeout_seconds=60)
    mgr.disconnect("sid-1")
    assert mgr.is_online("device-1") is False
    assert "sid-1" not in mgr._sid_to_device


def test_heartbeat_re_registers_after_sweep():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    mgr._last_seen["device-1"] = datetime.utcnow() - timedelta(seconds=120)
    mgr.sweep_stale(timeout_seconds=60)
    assert mgr.is_online("device-1") is False
    mgr.heartbeat("device-1", sid="sid-1")
    assert mgr.is_online("device-1") is True
    assert mgr._sid_to_device["sid-1"] == "device-1"


async def test_get_device_status(client, auth_headers):
    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=auth_headers)
    device_id = r.json()["device_id"]

    r = await client.get(f"/api/devices/{device_id}/status", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["device_id"] == device_id
    assert data["online"] is False
    assert data["last_seen_at"] is None
