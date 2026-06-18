from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, Device
from app.schemas import ContactCreate, ContactUpdate


class ContactError(Exception):
    pass


async def create_contact(
    db: AsyncSession, owner_id: str, device_id: str, payload: ContactCreate
) -> Contact:
    device_result = await db.execute(select(Device).where(Device.id == device_id, Device.owner_id == owner_id))
    device = device_result.scalar_one_or_none()
    if device is None:
        raise ContactError("Device not found")

    existing = await db.execute(
        select(Contact).where(Contact.device_id == device_id, Contact.button_index == payload.button_index)
    )
    if existing.scalar_one_or_none():
        raise ContactError("Button index already used")

    contact = Contact(
        device_id=device_id,
        user_id=payload.user_id,
        display_name=payload.display_name,
        button_index=payload.button_index,
    )
    db.add(contact)
    try:
        await db.commit()
        await db.refresh(contact)
    except IntegrityError as exc:
        await db.rollback()
        raise ContactError("Contact already exists") from exc
    return contact


async def get_contact(db: AsyncSession, owner_id: str, contact_id: str) -> Optional[Contact]:
    result = await db.execute(
        select(Contact).join(Device).where(Contact.id == contact_id, Device.owner_id == owner_id)
    )
    return result.scalar_one_or_none()


async def list_contacts(db: AsyncSession, owner_id: str, device_id: str) -> list[Contact]:
    device_result = await db.execute(select(Device).where(Device.id == device_id, Device.owner_id == owner_id))
    device = device_result.scalar_one_or_none()
    if device is None:
        raise ContactError("Device not found")
    result = await db.execute(select(Contact).where(Contact.device_id == device_id))
    return result.scalars().all()


async def update_contact(
    db: AsyncSession, owner_id: str, contact_id: str, payload: ContactUpdate
) -> Optional[Contact]:
    result = await db.execute(
        select(Contact).join(Device).where(Contact.id == contact_id, Device.owner_id == owner_id)
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        return None
    if payload.display_name is not None:
        contact.display_name = payload.display_name
    if payload.button_index is not None:
        contact.button_index = payload.button_index
    if payload.avatar_path is not None:
        contact.avatar_path = payload.avatar_path
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(db: AsyncSession, owner_id: str, contact_id: str) -> bool:
    result = await db.execute(
        select(Contact).join(Device).where(Contact.id == contact_id, Device.owner_id == owner_id)
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        return False
    await db.delete(contact)
    await db.commit()
    return True


async def is_contact(db: AsyncSession, device_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(Contact).where(Contact.device_id == device_id, Contact.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None
