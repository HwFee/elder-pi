import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Device
from app.socket.manager import manager


class SignalingNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ, auth):
        token = (auth or {}).get("token")
        if not token:
            raise ConnectionRefusedError("Missing token")

        async with AsyncSessionLocal() as db:
            device = await self._authenticate_device(db, token)
            if device is None:
                raise ConnectionRefusedError("Invalid token")
            manager.connect(sid, device.id)
            await self.enter_room(sid, manager.get_room_for_device(device.id))
            await self.save_session(sid, {"device_id": device.id})

    async def on_disconnect(self, sid):
        manager.disconnect(sid)

    async def on_presence_heartbeat(self, sid, data):
        session = await self.get_session(sid)
        device_id = session.get("device_id")
        if device_id:
            manager.heartbeat(device_id)

    async def _authenticate_device(self, db: AsyncSession, token: str):
        from jose import jwt, JWTError
        from app.config import get_settings

        try:
            payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
            device_id = payload.get("device_id")
            if device_id is None:
                return None
            return await db.get(Device, device_id)
        except JWTError:
            return None


signaling_ns = SignalingNamespace("/signaling")
