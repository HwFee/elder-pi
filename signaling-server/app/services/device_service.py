import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, User
from app.services.auth_service import hash_password


async def create_device(db: AsyncSession, owner: User, display_name: str) -> tuple[Device, str]:
    device_token = secrets.token_urlsafe(32)
    device = Device(
        owner_id=owner.id,
        display_name=display_name,
        device_token_hash=hash_password(device_token),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device, device_token


async def get_owned_device(db: AsyncSession, owner_id: str, device_id: str) -> Optional[Device]:
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.owner_id == owner_id)
    )
    return result.scalar_one_or_none()


async def list_devices(db: AsyncSession, owner_id: str) -> list[Device]:
    result = await db.execute(select(Device).where(Device.owner_id == owner_id))
    return result.scalars().all()


async def verify_device_token(db: AsyncSession, device_id: str, token: str) -> Optional[Device]:
    from app.services.auth_service import verify_password as verify_pwd

    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device and verify_pwd(token, device.device_token_hash):
        return device
    return None
