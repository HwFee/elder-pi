import pytest
from httpx import AsyncClient, ASGITransport

from app.db import async_engine, Base
from app.main import app
from app.socket.manager import manager
from app.socket.namespace import SignalingNamespace


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def reset_manager():
    manager._sid_to_device.clear()
    manager._device_to_sids.clear()
    manager._last_seen.clear()
    yield


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _register_user(client, email, password, full_name):
    await client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": full_name
    })
    r = await client.post("/api/auth/login", data={"username": email, "password": password})
    token = r.json()["access_token"]
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    return r.json()["id"], token


async def _create_device(client, owner_token, display_name="Pi"):
    headers = {"Authorization": f"Bearer {owner_token}"}
    r = await client.post("/api/devices", json={"display_name": display_name}, headers=headers)
    return r.json()["device_id"], r.json()["device_token"]


async def test_unauthorized_call_rejected(client):
    owner_id, owner_token = await _register_user(client, "alice@example.com", "secret", "Alice")
    stranger_id, stranger_token = await _register_user(client, "stranger@example.com", "secret", "Stranger")
    device_id, device_token = await _create_device(client, owner_token)

    ns = SignalingNamespace("/signaling")
    sessions = {}
    emitted = []

    async def save_session(sid, session):
        sessions[sid] = session

    async def get_session(sid):
        return sessions.get(sid, {})

    async def enter_room(sid, room):
        pass

    async def emit(event, data, room=None, skip_sid=None, **kwargs):
        emitted.append({"event": event, "data": data, "room": room, "skip_sid": skip_sid})

    ns.save_session = save_session
    ns.get_session = get_session
    ns.enter_room = enter_room
    ns.emit = emit

    sessions["stranger-sid"] = {"kind": "user", "user_id": stranger_id, "caller_name": "Stranger"}

    await ns.on_call_invite("stranger-sid", {
        "callId": "call-unauthorized",
        "toDeviceId": device_id,
        "offer": {"sdp": "fake"},
    })

    assert not any(e["event"] == "call:invite" for e in emitted)

    error = next(e for e in emitted if e["event"] == "call:error")
    assert error["room"] == "stranger-sid"
    assert error["data"]["reason"] == "Not in contact list"
