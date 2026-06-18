import asyncio
import os
import sys

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./elder-pi-smoke.db"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "signaling-server"))

from app.db import async_engine, AsyncSessionLocal, Base
from app.models import User, Device, Contact
from app.services.auth_service import create_access_token


async def main():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == "pi@example.com"))
        if existing:
            user = existing
        else:
            user = User(
                email="pi@example.com",
                hashed_password="not-used",
                full_name="Pi User",
            )
            db.add(user)
            await db.flush()

        device = Device(owner_id=user.id, display_name="Living Room Pi")
        db.add(device)
        await db.flush()

        contact = Contact(
            device_id=device.id,
            user_id=user.id,
            display_name="自己",
            button_index=1,
        )
        db.add(contact)
        await db.commit()

        token = create_access_token(data={"device_id": device.id})
        print(token)
        print(device.id)


if __name__ == "__main__":
    from sqlalchemy import select
    asyncio.run(main())
