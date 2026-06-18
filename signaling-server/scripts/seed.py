import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_engine, Base, AsyncSessionLocal
from app.models import User, Device
from app.schemas import UserCreate
from app.services.auth_service import hash_password
from app.services.device_service import create_device


async def seed():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        user = User(email="demo@example.com", hashed_password=hash_password("demo"), full_name="Demo User")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        device, token = await create_device(db, user, "Demo Pi")
        print(f"User ID: {user.id}")
        print(f"Device ID: {device.id}")
        print(f"Device Token: {token}")


if __name__ == "__main__":
    asyncio.run(seed())
