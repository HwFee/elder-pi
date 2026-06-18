import pytest
import socketio
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from app.db import async_engine, AsyncSessionLocal, Base
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


async def test_device_socket_connects_with_token(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_token = r.json()["device_token"]

    ns = SignalingNamespace("/signaling")
    sessions = {}
    rooms = {}

    async def save_session(sid, session):
        sessions[sid] = session

    async def get_session(sid):
        return sessions.get(sid, {})

    async def enter_room(sid, room):
        rooms.setdefault(sid, set()).add(room)

    ns.save_session = save_session
    ns.get_session = get_session
    ns.enter_room = enter_room

    await ns.on_connect("test-sid", {}, {"token": device_token})
    assert sessions["test-sid"]["kind"] == "device"
    assert "device_id" in sessions["test-sid"]
    assert f"device:{sessions['test-sid']['device_id']}" in rooms["test-sid"]


async def test_user_socket_connects_with_token(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    user_token = r.json()["access_token"]

    ns = SignalingNamespace("/signaling")
    sessions = {}

    async def save_session(sid, session):
        sessions[sid] = session

    async def get_session(sid):
        return sessions.get(sid, {})

    async def enter_room(sid, room):
        pass

    ns.save_session = save_session
    ns.get_session = get_session
    ns.enter_room = enter_room

    await ns.on_connect("test-sid", {}, {"token": user_token})
    assert sessions["test-sid"]["kind"] == "user"
    assert "user_id" in sessions["test-sid"]


async def test_socket_rejects_missing_token(client):
    ns = SignalingNamespace("/signaling")
    with pytest.raises(ConnectionRefusedError):
        await ns.on_connect("test-sid", {}, {})


async def test_socket_app_exposed():
    from app.main import socket_app
    assert socket_app is not None


async def test_heartbeat_re_registers_after_stale_sweep(client):
    manager._sid_to_device.clear()
    manager._device_to_sids.clear()
    manager._last_seen.clear()

    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_token = r.json()["device_token"]

    ns = SignalingNamespace("/signaling")
    sessions = {}
    rooms = {}

    async def save_session(sid, session):
        sessions[sid] = session

    async def get_session(sid):
        return sessions.get(sid, {})

    async def enter_room(sid, room):
        rooms.setdefault(sid, set()).add(room)

    ns.save_session = save_session
    ns.get_session = get_session
    ns.enter_room = enter_room

    await ns.on_connect("test-sid", {}, {"token": device_token})
    device_id = sessions["test-sid"]["device_id"]

    manager._last_seen[device_id] = datetime.utcnow() - timedelta(seconds=120)
    manager.sweep_stale(timeout_seconds=60)
    assert manager.is_online(device_id) is False

    await ns.on_presence_heartbeat("test-sid", {})
    assert manager.is_online(device_id) is True
    assert manager._sid_to_device["test-sid"] == device_id


async def test_call_session_lifecycle(client):
    from app.services import call_service

    owner_id, owner_token = await _register_user(client, "owner@example.com", "secret", "Owner")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")
    device_id, _ = await _create_device(client, owner_token)

    async with AsyncSessionLocal() as db:
        call = await call_service.create_call_session(db, "call-1", caller_id, device_id)
        assert call.call_id == "call-1"
        assert call.caller_id == caller_id
        assert call.callee_device_id == device_id
        assert call.status == "pending"

        accepted = await call_service.accept_call(db, "call-1")
        assert accepted.status == "accepted"

        rejected = await call_service.reject_call(db, "call-1")
        assert rejected.status == "rejected"
        assert rejected.ended_at is not None

        call2 = await call_service.create_call_session(db, "call-2", caller_id, device_id)
        ended = await call_service.end_call(db, "call-2")
        assert ended.status == "ended"
        assert ended.ended_at is not None


async def test_call_invite_forwarded_to_device(client):
    owner_id, owner_token = await _register_user(client, "owner@example.com", "secret", "Owner")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")
    device_id, _ = await _create_device(client, owner_token)
    await client.post(
        f"/api/devices/{device_id}/contacts",
        json={"user_id": caller_id, "display_name": "Caller", "button_index": 1},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    ns, sessions, rooms, emitted = _make_namespace()
    sessions["caller-sid"] = {"kind": "user", "user_id": caller_id, "caller_name": "Caller"}

    await ns.on_call_invite("caller-sid", {
        "callId": "call-1",
        "toDeviceId": device_id,
        "offer": {"sdp": "fake-offer"},
    })

    invite = next(e for e in emitted if e["event"] == "call:invite")
    assert invite["room"] == manager.get_room_for_device(device_id)
    assert invite["data"]["callId"] == "call-1"
    assert invite["data"]["callerId"] == caller_id
    assert invite["data"]["callerName"] == "Caller"
    assert invite["data"]["offer"] == {"sdp": "fake-offer"}


async def test_call_accept_forwarded_to_caller(client):
    from app.services import call_service

    owner_id, owner_token = await _register_user(client, "owner@example.com", "secret", "Owner")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")
    device_id, _ = await _create_device(client, owner_token)

    async with AsyncSessionLocal() as db:
        await call_service.create_call_session(db, "call-1", caller_id, device_id)

    ns, sessions, rooms, emitted = _make_namespace()
    sessions["device-sid"] = {"kind": "device", "device_id": device_id}

    await ns.on_call_accept("device-sid", {"callId": "call-1", "answer": {"sdp": "fake-answer"}})

    accept = next(e for e in emitted if e["event"] == "call:accept")
    assert accept["room"] == f"user:{caller_id}"
    assert accept["data"]["callId"] == "call-1"
    assert accept["data"]["answer"] == {"sdp": "fake-answer"}


async def test_call_reject_forwarded_to_caller(client):
    from app.services import call_service

    owner_id, owner_token = await _register_user(client, "owner@example.com", "secret", "Owner")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")
    device_id, _ = await _create_device(client, owner_token)

    async with AsyncSessionLocal() as db:
        await call_service.create_call_session(db, "call-1", caller_id, device_id)

    ns, sessions, rooms, emitted = _make_namespace()
    sessions["device-sid"] = {"kind": "device", "device_id": device_id}

    await ns.on_call_reject("device-sid", {"callId": "call-1", "reason": "declined"})

    reject = next(e for e in emitted if e["event"] == "call:reject")
    assert reject["room"] == f"user:{caller_id}"
    assert reject["data"]["callId"] == "call-1"
    assert reject["data"]["reason"] == "declined"


async def test_call_end_forwarded_to_both(client):
    from app.services import call_service

    owner_id, owner_token = await _register_user(client, "owner@example.com", "secret", "Owner")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")
    device_id, _ = await _create_device(client, owner_token)

    async with AsyncSessionLocal() as db:
        await call_service.create_call_session(db, "call-1", caller_id, device_id)

    ns, sessions, rooms, emitted = _make_namespace()
    sessions["caller-sid"] = {"kind": "user", "user_id": caller_id}

    await ns.on_call_end("caller-sid", {"callId": "call-1"})

    ends = [e for e in emitted if e["event"] == "call:end"]
    assert len(ends) == 2
    rooms_hit = {e["room"] for e in ends}
    assert rooms_hit == {f"user:{caller_id}", manager.get_room_for_device(device_id)}


async def test_ice_candidate_forwarded_to_other_party(client):
    from app.services import call_service

    owner_id, owner_token = await _register_user(client, "owner@example.com", "secret", "Owner")
    caller_id, caller_token = await _register_user(client, "caller@example.com", "secret", "Caller")
    device_id, _ = await _create_device(client, owner_token)

    async with AsyncSessionLocal() as db:
        await call_service.create_call_session(db, "call-1", caller_id, device_id)

    ns, sessions, rooms, emitted = _make_namespace()
    sessions["device-sid"] = {"kind": "device", "device_id": device_id}

    await ns.on_ice_candidate("device-sid", {"callId": "call-1", "candidate": "candidate-1"})

    ice = next(e for e in emitted if e["event"] == "ice:candidate")
    assert ice["room"] == f"user:{caller_id}"
    assert ice["data"]["candidate"] == "candidate-1"
    assert ice["skip_sid"] == "device-sid"

    emitted.clear()
    sessions["caller-sid"] = {"kind": "user", "user_id": caller_id}
    await ns.on_ice_candidate("caller-sid", {"callId": "call-1", "candidate": "candidate-2"})

    ice2 = next(e for e in emitted if e["event"] == "ice:candidate")
    assert ice2["room"] == manager.get_room_for_device(device_id)
    assert ice2["data"]["candidate"] == "candidate-2"
    assert ice2["skip_sid"] == "caller-sid"
