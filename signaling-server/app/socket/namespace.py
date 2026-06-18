import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Device, User
from app.services.auth_service import decode_access_token
from app.socket.manager import manager


class SignalingNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ, auth):
        token = (auth or {}).get("token")
        if not token:
            raise ConnectionRefusedError("Missing token")

        async with AsyncSessionLocal() as db:
            payload = decode_access_token(token)
            if payload is None:
                raise ConnectionRefusedError("Invalid token")

            session = {}
            if "device_id" in payload:
                device = await db.get(Device, payload["device_id"])
                if device is None:
                    raise ConnectionRefusedError("Device not found")
                session["device_id"] = device.id
                session["kind"] = "device"
            elif "sub" in payload:
                user = await db.get(User, payload["sub"])
                if user is None:
                    raise ConnectionRefusedError("User not found")
                session["user_id"] = user.id
                session["kind"] = "user"
            else:
                raise ConnectionRefusedError("Invalid token claims")

            await self.save_session(sid, session)
            device_id = session.get("device_id")
            if device_id:
                manager.connect(sid, device_id)
                await self.enter_room(sid, manager.get_room_for_device(device_id))

    async def on_disconnect(self, sid):
        manager.disconnect(sid)

    async def on_presence_heartbeat(self, sid, data):
        session = await self.get_session(sid)
        device_id = session.get("device_id")
        if device_id:
            manager.heartbeat(device_id, sid)


signaling_ns = SignalingNamespace("/signaling")
