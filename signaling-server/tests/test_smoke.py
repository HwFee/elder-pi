import pytest
import uuid
from httpx import AsyncClient, ASGITransport

from app.db import async_engine, AsyncSessionLocal, Base
from app.main import app
from app.services import call_service
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


def _make_namespace():
    ns = SignalingNamespace("/signaling")
    sessions = {}
    rooms = {}
    emitted = []

    async def save_session(sid, session):
        sessions[sid] = session

    async def get_session(sid):
        return sessions.get(sid, {})

    async def enter_room(sid, room):
        rooms.setdefault(sid, set()).add(room)

    async def emit(event, data, room=None, skip_sid=None, **kwargs):
        emitted.append({"event": event, "data": data, "room": room, "skip_sid": skip_sid})

    ns.save_session = save_session
    ns.get_session = get_session
    ns.enter_room = enter_room
    ns.emit = emit
    return ns, sessions, rooms, emitted


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


async def test_end_to_end_call_smoke(client):
    callee_id, callee_token = await _register_user(client, "callee@example.com", "secret", "Callee")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")

    device_id, device_token = await _create_device(client, callee_token, "Callee Pi")

    await client.post(
        f"/api/devices/{device_id}/contacts",
        json={"user_id": caller_id, "display_name": "Caller", "button_index": 1},
        headers={"Authorization": f"Bearer {callee_token}"},
    )

    ns, sessions, rooms, emitted = _make_namespace()

    await ns.on_connect("caller-sid", {}, {"token": caller_token})
    await ns.on_connect("device-sid", {}, {"token": device_token})

    caller_session = sessions["caller-sid"]
    device_session = sessions["device-sid"]
    assert caller_session["kind"] == "user"
    assert device_session["kind"] == "device"

    call_id = str(uuid.uuid4())

    await ns.on_call_invite("caller-sid", {
        "callId": call_id,
        "toDeviceId": device_id,
        "offer": {"type": "offer", "sdp": "fake-offer"},
    })

    invite_events = [e for e in emitted if e["event"] == "call:invite"]
    assert len(invite_events) == 1
    invite = invite_events[0]
    assert invite["room"] == manager.get_room_for_device(device_id)
    assert invite["data"]["callId"] == call_id
    assert invite["data"]["callerId"] == caller_id

    async with AsyncSessionLocal() as db:
        session = await call_service.get_call_session(db, call_id)
        assert session.status == "pending"

    emitted.clear()
    await ns.on_call_accept("device-sid", {
        "callId": call_id,
        "answer": {"type": "answer", "sdp": "fake-answer"},
    })

    accept_events = [e for e in emitted if e["event"] == "call:accept"]
    assert len(accept_events) == 1
    accept = accept_events[0]
    assert accept["room"] == f"user:{caller_id}"
    assert accept["data"]["callId"] == call_id
    assert accept["data"]["answer"]["sdp"] == "fake-answer"

    async with AsyncSessionLocal() as db:
        session = await call_service.get_call_session(db, call_id)
        assert session.status == "accepted"

    emitted.clear()
    await ns.on_call_end("caller-sid", {"callId": call_id})

    end_events = [e for e in emitted if e["event"] == "call:end"]
    assert len(end_events) == 2
    end_rooms = {e["room"] for e in end_events}
    assert end_rooms == {f"user:{caller_id}", manager.get_room_for_device(device_id)}

    async with AsyncSessionLocal() as db:
        session = await call_service.get_call_session(db, call_id)
        assert session.status == "ended"
        assert session.ended_at is not None

    await ns.on_disconnect("caller-sid")
    await ns.on_disconnect("device-sid")
