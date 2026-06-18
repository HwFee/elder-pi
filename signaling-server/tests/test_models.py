import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_engine, Base, AsyncSessionLocal
from app.models import User, Device


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_user():
    async with AsyncSessionLocal() as session:
        user = User(email="alice@example.com", hashed_password="hash", full_name="Alice")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        assert user.id is not None
        assert user.email == "alice@example.com"
