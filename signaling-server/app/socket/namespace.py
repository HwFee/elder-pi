import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Device, User
from app.services import call_service, contact_service
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
                session["caller_name"] = user.full_name
            else:
                raise ConnectionRefusedError("Invalid token claims")

            await self.save_session(sid, session)
            device_id = session.get("device_id")
            if device_id:
                manager.connect(sid, device_id)
                await self.enter_room(sid, manager.get_room_for_device(device_id))
            elif session.get("kind") == "user":
                await self.enter_room(sid, f"user:{session['user_id']}")

    async def on_disconnect(self, sid):
        manager.disconnect(sid)

    async def on_presence_heartbeat(self, sid, data):
        session = await self.get_session(sid)
        device_id = session.get("device_id")
        if device_id:
            manager.heartbeat(device_id, sid)

    async def on_call_invite(self, sid, data):
        async with AsyncSessionLocal() as db:
            session = await self.get_session(sid)
            caller_id = session.get("user_id")
            if caller_id is None:
                await self.emit(
                    "call:error",
                    {"callId": data.get("callId"), "reason": "Only users can call"},
                    room=sid,
                )
                return

            call_id = data.get("callId")
            to_device_id = data.get("toDeviceId")
            offer = data.get("offer")

            if not call_id or not to_device_id:
                await self.emit(
                    "call:error",
                    {"callId": call_id, "reason": "Missing callId or toDeviceId"},
                    room=sid,
                )
                return

            is_allowed = await contact_service.is_contact(db, to_device_id, caller_id)
            if not is_allowed:
                await self.emit(
                    "call:error",
                    {"callId": call_id, "reason": "Not in contact list"},
                    room=sid,
                )
                return

            active = await call_service.get_active_call_for_device(db, to_device_id)
            if active is not None and active.call_id != call_id:
                await self.emit("call:busy", {"callId": call_id}, room=sid)
                return

            existing = await call_service.get_call_session(db, call_id)
            if existing is not None and existing.status in ("pending", "accepted"):
                await self.emit("call:busy", {"callId": call_id}, room=sid)
                return

            await call_service.create_call_session(db, call_id, caller_id, to_device_id)
            await self.emit(
                "call:invite",
                {
                    "callId": call_id,
                    "callerId": caller_id,
                    "callerName": session.get("caller_name", "Caller"),
                    "offer": offer,
                },
                room=manager.get_room_for_device(to_device_id),
            )

    async def on_call_accept(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session_rec = await call_service.get_call_session(db, call_id)
            if session_rec is None:
                return
            await call_service.accept_call(db, call_id)
            await self.emit(
                "call:accept",
                {"callId": call_id, "answer": data.get("answer")},
                room=f"user:{session_rec.caller_id}",
            )

    async def on_call_reject(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session_rec = await call_service.get_call_session(db, call_id)
            if session_rec is None:
                return
            await call_service.reject_call(db, call_id)
            await self.emit(
                "call:reject",
                {"callId": call_id, "reason": data.get("reason")},
                room=f"user:{session_rec.caller_id}",
            )

    async def on_call_end(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session_rec = await call_service.get_call_session(db, call_id)
            if session_rec is None:
                return
            await call_service.end_call(db, call_id)
            await self.emit("call:end", {"callId": call_id}, room=f"user:{session_rec.caller_id}")
            await self.emit(
                "call:end",
                {"callId": call_id},
                room=manager.get_room_for_device(session_rec.callee_device_id),
            )

    async def on_ice_candidate(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session_rec = await call_service.get_call_session(db, call_id)
            if session_rec is None:
                return
            caller_session = await self.get_session(sid)
            if caller_session.get("user_id") == session_rec.caller_id:
                target_room = manager.get_room_for_device(session_rec.callee_device_id)
            else:
                target_room = f"user:{session_rec.caller_id}"
            await self.emit(
                "ice:candidate",
                {"callId": call_id, "candidate": data.get("candidate")},
                room=target_room,
                skip_sid=sid,
            )


signaling_ns = SignalingNamespace("/signaling")
