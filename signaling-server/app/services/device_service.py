from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, User
from app.services.auth_service import create_access_token


def create_device_token(device_id: str) -> str:
    return create_access_token({"device_id": device_id})


async def create_device(db: AsyncSession, owner: User, display_name: str) -> tuple[Device, str]:
    device = Device(
        owner_id=owner.id,
        display_name=display_name,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device, create_device_token(device.id)


async def get_owned_device(db: AsyncSession, owner_id: str, device_id: str) -> Optional[Device]:
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.owner_id == owner_id)
    )
    return result.scalar_one_or_none()


async def list_devices(db: AsyncSession, owner_id: str) -> list[Device]:
    result = await db.execute(select(Device).where(Device.owner_id == owner_id))
    return result.scalars().all()
