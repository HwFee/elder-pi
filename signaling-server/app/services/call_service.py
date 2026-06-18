from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CallSession


async def create_call_session(
    db: AsyncSession, call_id: str, caller_id: str, callee_device_id: str
) -> CallSession:
    session = CallSession(
        call_id=call_id,
        caller_id=caller_id,
        callee_device_id=callee_device_id,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_call_session(db: AsyncSession, call_id: str) -> Optional[CallSession]:
    result = await db.execute(select(CallSession).where(CallSession.call_id == call_id))
    return result.scalar_one_or_none()


async def accept_call(db: AsyncSession, call_id: str) -> Optional[CallSession]:
    session = await get_call_session(db, call_id)
    if session is None:
        return None
    session.status = "accepted"
    await db.commit()
    await db.refresh(session)
    return session


async def reject_call(db: AsyncSession, call_id: str) -> Optional[CallSession]:
    session = await get_call_session(db, call_id)
    if session is None:
        return None
    session.status = "rejected"
    session.ended_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


async def end_call(db: AsyncSession, call_id: str) -> Optional[CallSession]:
    session = await get_call_session(db, call_id)
    if session is None:
        return None
    session.status = "ended"
    session.ended_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


async def get_active_call_for_device(db: AsyncSession, device_id: str) -> Optional[CallSession]:
    result = await db.execute(
        select(CallSession)
        .where(
            CallSession.callee_device_id == device_id,
            CallSession.status.in_(["pending", "accepted"]),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def is_active_call(db: AsyncSession, device_id: str) -> Optional[str]:
    active = await get_active_call_for_device(db, device_id)
    return active.call_id if active else None
