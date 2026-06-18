import pytest
import socketio
from httpx import AsyncClient, ASGITransport

from app.db import async_engine, Base
from app.main import app
from app.socket.namespace import SignalingNamespace


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
