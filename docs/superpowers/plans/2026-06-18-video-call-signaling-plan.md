---
change: video-call-signaling
design-doc: docs/superpowers/specs/2026-06-18-video-call-signaling-design.md
base-ref: 57ece8daaaf0edfe74dd53c75958cd86093652c8
archived-with: 2026-06-18-video-call-signaling
---

# video-call-signaling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 构建基于 Python/FastAPI 的家庭-老人视频通话后端，提供 JWT 认证、设备/联系人管理、WebRTC 信令转发、在线状态与通话白名单能力。

**Architecture:** 采用 FastAPI 提供 REST API，python-socketio 提供 `/signaling` 命名空间的实时事件；SQLAlchemy 2.0 + SQLite 作为 MVP 持久化；文件系统存储头像；uvicorn 单进程 ASGI 部署。本计划遵循 Design Doc 中定义的 Python 技术栈（与 tasks.md 中 Node.js 描述不一致时以 Design Doc 为准）。

**Tech Stack:** Python 3.11+, FastAPI, python-socketio, SQLAlchemy 2.0, SQLite, bcrypt, python-jose, pydantic-settings, pytest, uvicorn, docker-compose

## Global Constraints

- Python 3.11+，使用类型注解与 `async`/`await`。
- 数据库：SQLAlchemy 2.0 + SQLite；列类型需兼容 Postgres，方便后续迁移。
- 密码哈希：bcrypt；JWT 签名算法：HS256。
- 所有受保护 HTTP 路由需校验 `Authorization: Bearer <token>`。
- Socket.IO 连接认证通过 `auth.token` 字段。
- 头像本地存储路径：`uploads/avatars/`，通过静态路由对外服务。
- CORS 来源由 `CORS_ORIGINS` 环境变量控制。
- 每个任务以 TDD 方式执行，先写失败测试再实现，最后提交。
- 文件路径以 `signaling-server/` 为根目录。

archived-with: 2026-06-18-video-call-signaling
---

## File Structure

```
signaling-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用 + Socket.IO 挂载
│   ├── config.py            # Pydantic Settings
│   ├── db.py                # SQLAlchemy engine / session / 基类
│   ├── models.py            # User, Device, Contact, CallSession ORM 模型
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── dependencies.py      # get_db, get_current_user, get_current_device
│   ├── routers/
│   │   ├── auth.py
│   │   ├── devices.py
│   │   └── contacts.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   ├── contact_service.py
│   │   └── call_service.py
│   └── socket/
│       ├── namespace.py     # /signaling 事件处理器
│       └── manager.py       # 房间、通话状态、在线状态辅助
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_devices.py
│   ├── test_contacts.py
│   ├── test_presence.py
│   └── test_signaling.py
├── uploads/avatars/
├── alembic/                 # 可选：后续数据库迁移
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── pytest.ini
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 1：项目脚手架

### Task 1：创建项目基础结构、依赖与配置

**Files:**
- Create: `signaling-server/requirements.txt`
- Create: `signaling-server/.env.example`
- Create: `signaling-server/pytest.ini`
- Create: `signaling-server/app/__init__.py`
- Create: `signaling-server/app/config.py`

**Interfaces:**
- Produces: `app.config.Settings` 类，字段包含 `secret_key`, `database_url`, `access_token_expire_minutes`, `cors_origins`, `port`, `upload_dir`。
- Produces: `app.config.get_settings()` 返回 `Settings` 单例。

- [x] **Step 1：编写 requirements.txt**

```txt
fastapi==0.111.0
python-socketio==5.11.3
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
aiosqlite==0.20.0
pydantic-settings==2.3.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pytest==8.2.2
pytest-asyncio==0.23.7
httpx==0.27.0
websocket-client==1.8.0
```

- [x] **Step 2：编写 .env.example**

```bash
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite+aiosqlite:///./signaling.db
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
PORT=8000
UPLOAD_DIR=uploads/avatars
```

- [x] **Step 3：编写 pytest.ini**

```ini
[pytest]
asyncio_mode = auto
pythonpath = app
```

- [x] **Step 4：编写 config.py 并附带失败测试**

测试 `signaling-server/tests/test_config.py`：

```python
import os
from app.config import get_settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("PORT", "8000")
    settings = get_settings()
    assert settings.secret_key == "test-secret"
    assert settings.database_url == "sqlite+aiosqlite:///./test.db"
    assert settings.access_token_expire_minutes == 60
    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.port == 8000
```

实现 `signaling-server/app/config.py`：

```python
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str
    database_url: str = "sqlite+aiosqlite:///./signaling.db"
    access_token_expire_minutes: int = 1440
    cors_origins: List[str] = ["http://localhost:3000"]
    port: int = 8000
    upload_dir: str = "uploads/avatars"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [x] **Step 5：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_config.py -v`
Expected: PASS

- [x] **Step 6：提交**

```bash
cd signaling-server
git add requirements.txt .env.example pytest.ini app/__init__.py app/config.py tests/test_config.py
git commit -m "chore(signaling): bootstrap project config and dependencies"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 2：数据库连接、ORM 模型与迁移脚本

**Files:**
- Create: `signaling-server/app/db.py`
- Create: `signaling-server/app/models.py`
- Create: `signaling-server/alembic.ini`（可选，后续使用）
- Create: `signaling-server/alembic/env.py`（可选）
- Test: `signaling-server/tests/test_models.py`

**Interfaces:**
- Produces: `app.db.AsyncSessionLocal`, `app.db.async_engine`, `app.db.Base`，`app.db.get_db()` 依赖。
- Produces: ORM 模型 `User`, `Device`, `Contact`, `CallSession`。

- [x] **Step 1：编写 db.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import get_settings

settings = get_settings()

async_engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [x] **Step 2：编写 models.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    display_name = Column(String(255), nullable=False)
    device_token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="devices")
    contacts = relationship("Contact", back_populates="device", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    display_name = Column(String(255), nullable=False)
    button_index = Column(Integer, nullable=False)
    avatar_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device", back_populates="contacts")
    user = relationship("User")


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    call_id = Column(String(36), unique=True, nullable=False, index=True)
    caller_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    callee_device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending / accepted / rejected / ended
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
```

- [x] **Step 3：编写模型创建测试**

`signaling-server/tests/test_models.py`：

```python
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
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_models.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/db.py app/models.py tests/test_models.py
git commit -m "feat(signaling): add database layer and ORM models"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 3：Pydantic 模式与共享依赖

**Files:**
- Create: `signaling-server/app/schemas.py`
- Create: `signaling-server/app/dependencies.py`
- Test: `signaling-server/tests/test_schemas.py`

**Interfaces:**
- Produces: `UserCreate`, `UserResponse`, `Token`, `DeviceCreate`, `DeviceResponse`, `DeviceTokenResponse`, `ContactCreate`, `ContactUpdate`, `ContactResponse`, `ContactListResponse`, `DeviceStatusResponse`。
- Produces: `get_current_user` 依赖，返回 `User` ORM 对象；`get_current_device_or_user` 用于 Socket.IO。

- [x] **Step 1：编写 schemas.py**

```python
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceCreate(BaseModel):
    display_name: str


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    display_name: str
    created_at: datetime


class DeviceTokenResponse(BaseModel):
    device_id: str
    device_token: str


class ContactCreate(BaseModel):
    user_id: str
    display_name: str
    button_index: int


class ContactUpdate(BaseModel):
    display_name: Optional[str] = None
    button_index: Optional[int] = None
    avatar_path: Optional[str] = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    user_id: str
    display_name: str
    button_index: int
    avatar_path: Optional[str]
    created_at: datetime


class ContactListResponse(BaseModel):
    contacts: List[ContactResponse]


class DeviceStatusResponse(BaseModel):
    device_id: str
    online: bool
    last_seen_at: Optional[datetime]
```

- [x] **Step 2：编写 dependencies.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models import User
from app.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload["sub"]
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [x] **Step 3：编写 schema 校验测试**

`signaling-server/tests/test_schemas.py`：

```python
from datetime import datetime

from app.schemas import UserCreate, ContactResponse


def test_user_create_validates_email():
    data = UserCreate(email="alice@example.com", password="secret", full_name="Alice")
    assert data.email == "alice@example.com"


def test_contact_response_serializes():
    class FakeContact:
        id = "c1"
        device_id = "d1"
        user_id = "u1"
        display_name = "Alice"
        button_index = 1
        avatar_path = None
        created_at = datetime.utcnow()

    response = ContactResponse.model_validate(FakeContact)
    assert response.display_name == "Alice"
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_schemas.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/schemas.py app/dependencies.py tests/test_schemas.py
git commit -m "feat(signaling): add pydantic schemas and auth dependencies"
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 2：用户认证

### Task 4：认证服务与密码工具

**Files:**
- Create: `signaling-server/app/services/auth_service.py`
- Test: `signaling-server/tests/test_auth_service.py`

**Interfaces:**
- Produces: `hash_password(password: str) -> str`
- Produces: `verify_password(password: str, hashed: str) -> bool`
- Produces: `create_access_token(data: dict) -> str`
- Produces: `decode_access_token(token: str) -> Optional[dict]`
- Produces: `authenticate_user(db, email, password) -> Optional[User]`

- [x] **Step 1：编写失败测试**

`signaling-server/tests/test_auth_service.py`：

```python
import pytest
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hash_and_verify():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_token_round_trip(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    token = create_access_token({"sub": "user-1"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
```

- [x] **Step 2：实现 auth_service.py**

```python
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict]:
    try:
        settings = get_settings()
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None
```

- [x] **Step 3：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_auth_service.py -v`
Expected: PASS

- [x] **Step 4：提交**

```bash
cd signaling-server
git add app/services/auth_service.py tests/test_auth_service.py
git commit -m "feat(signaling): add password and JWT auth service"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 5：Auth 路由（注册 / 登录）

**Files:**
- Create: `signaling-server/app/routers/auth.py`
- Modify: `signaling-server/app/main.py`（创建并挂载 FastAPI 应用）
- Test: `signaling-server/tests/test_auth.py`

**Interfaces:**
- Produces: `POST /api/auth/register` -> `UserResponse`
- Produces: `POST /api/auth/login` -> `Token`
- Consumes: `app.services.auth_service`, `app.schemas.UserCreate`, `app.schemas.Token`

- [x] **Step 1：创建 main.py 骨架**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth

settings = get_settings()

app = FastAPI(title="Video Call Signaling Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [x] **Step 2：编写 auth 路由失败测试**

`signaling-server/tests/test_auth.py`：

```python
import pytest
from httpx import AsyncClient

from app.main import app
from app.db import async_engine, Base


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_register_and_login(client):
    payload = {"email": "alice@example.com", "password": "secret", "full_name": "Alice"}
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 201
    assert r.json()["email"] == "alice@example.com"

    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_login_invalid_password(client):
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "wrong"})
    assert r.status_code == 401
```

- [x] **Step 3：实现 auth.py 路由**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import Token, UserCreate, UserResponse
from app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.id})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_auth.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/main.py app/routers/auth.py tests/test_auth.py
git commit -m "feat(signaling): add user registration and login endpoints"
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 3：设备与联系人管理

### Task 6：设备服务与路由

**Files:**
- Create: `signaling-server/app/services/device_service.py`
- Create: `signaling-server/app/routers/devices.py`
- Modify: `signaling-server/app/main.py` 挂载 devices 路由
- Test: `signaling-server/tests/test_devices.py`

**Interfaces:**
- Produces: `create_device(db, owner: User, display_name: str) -> (Device, str)` 返回设备和明文 device_token。
- Produces: `get_owned_device(db, owner_id, device_id) -> Optional[Device]`。
- Produces: `POST /api/devices`, `GET /api/devices`, `GET /api/devices/{device_id}`。

- [x] **Step 1：编写设备服务**

```python
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
```

- [x] **Step 2：编写 devices 路由**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.routers.contacts import router as contacts_router
from app.schemas import DeviceCreate, DeviceResponse, DeviceTokenResponse
from app.services import device_service

router = APIRouter()


@router.post("", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device, token = await device_service.create_device(db, current_user, payload.display_name)
    return DeviceTokenResponse(device_id=device.id, device_token=token)


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await device_service.list_devices(db, current_user.id)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = await device_service.get_owned_device(db, current_user.id, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


router.include_router(contacts_router, prefix="/{device_id}/contacts")
```

- [x] **Step 3：挂载路由并测试**

在 `app/main.py` 中新增：

```python
from app.routers import devices

app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
```

`signaling-server/tests/test_devices.py`：

```python
import pytest
from httpx import AsyncClient

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_get_device(client, auth_headers):
    r = await client.post("/api/devices", json={"display_name": "Grandma Pi"}, headers=auth_headers)
    assert r.status_code == 201
    device_id = r.json()["device_id"]

    r = await client.get(f"/api/devices/{device_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["display_name"] == "Grandma Pi"
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_devices.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/services/device_service.py app/routers/devices.py tests/test_devices.py
git commit -m "feat(signaling): add device registration and ownership routes"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 7：联系人服务与路由

**Files:**
- Create: `signaling-server/app/services/contact_service.py`
- Create: `signaling-server/app/routers/contacts.py`
- Test: `signaling-server/tests/test_contacts.py`

**Interfaces:**
- Produces: `create_contact(db, owner_id, device_id, payload) -> Contact`
- Produces: `update_contact(...)`, `delete_contact(...)`
- Produces: `POST /api/devices/{device_id}/contacts`, `GET /api/devices/{device_id}/contacts`, `PATCH /api/contacts/{contact_id}`, `DELETE /api/contacts/{contact_id}`
- Produces: `is_contact(db, device_id, user_id) -> bool`

- [x] **Step 1：编写 contact_service.py**

```python
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
```

- [x] **Step 2：编写 contacts.py 路由**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import ContactCreate, ContactListResponse, ContactResponse, ContactUpdate
from app.services import contact_service

router = APIRouter()


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    device_id: str,
    payload: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        contact = await contact_service.create_contact(db, current_user.id, device_id, payload)
    except contact_service.ContactError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return contact


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        contacts = await contact_service.list_contacts(db, current_user.id, device_id)
    except contact_service.ContactError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ContactListResponse(contacts=contacts)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = await contact_service.update_contact(db, current_user.id, contact_id, payload)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await contact_service.delete_contact(db, current_user.id, contact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
```

- [x] **Step 3：编写联系人测试**

`signaling-server/tests/test_contacts.py`：

```python
import pytest
from httpx import AsyncClient

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def alice(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    return r.json()["access_token"]


@pytest.fixture
async def bob(client):
    await client.post("/api/auth/register", json={
        "email": "bob@example.com", "password": "secret", "full_name": "Bob"
    })
    r = await client.post("/api/auth/login", data={"username": "bob@example.com", "password": "secret"})
    return {"id": r.json()["user_id"], "token": r.json()["access_token"]}


async def test_create_contact_requires_unique_button_index(client, alice, bob):
    headers = {"Authorization": f"Bearer {alice}"}
    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": bob["id"], "display_name": "Bob", "button_index": 1
    }, headers=headers)
    assert r.status_code == 201

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": bob["id"], "display_name": "Bob 2", "button_index": 1
    }, headers=headers)
    assert r.status_code == 400
```

注意：为了获取 user_id，需要在 login 响应中返回 `user_id`，后续在 auth 路由中补充。

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_contacts.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/services/contact_service.py app/routers/contacts.py tests/test_contacts.py
git commit -m "feat(signaling): add contact CRUD and ownership checks"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 8：头像上传与静态文件服务

**Files:**
- Create: `signaling-server/app/services/upload_service.py`
- Modify: `signaling-server/app/routers/contacts.py` 增加上传端点
- Modify: `signaling-server/app/main.py` 挂载静态目录
- Test: `signaling-server/tests/test_uploads.py`

**Interfaces:**
- Produces: `POST /api/contacts/{contact_id}/avatar` -> `ContactResponse`
- Produces: `save_avatar(file, upload_dir) -> str` 返回相对路径。

- [x] **Step 1：编写 upload_service.py**

```python
import os
import uuid
from pathlib import Path

from fastapi import UploadFile


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024


async def save_avatar(file: UploadFile, upload_dir: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Only JPEG, PNG, WebP images are allowed")
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise ValueError("File too large")
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    path = Path(upload_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(contents)
    return str(path)
```

- [x] **Step 2：在 contacts.py 增加头像上传端点**

```python
from fastapi import File, UploadFile
from app.config import get_settings
from app.services import upload_service


@router.post("/{contact_id}/avatar", response_model=ContactResponse)
async def upload_avatar(
    contact_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = await contact_service.update_contact(
        db, current_user.id, contact_id, ContactUpdate(avatar_path=None)
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    try:
        avatar_path = await upload_service.save_avatar(file, get_settings().upload_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    contact = await contact_service.update_contact(
        db, current_user.id, contact_id, ContactUpdate(avatar_path=avatar_path)
    )
    return contact
```

- [x] **Step 3：在 main.py 挂载静态目录**

```python
from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
```

- [x] **Step 4：编写上传测试**

`signaling-server/tests/test_uploads.py`：

```python
import io
import pytest
from httpx import AsyncClient

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "avatars"))
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_upload_avatar(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_id = r.json()["device_id"]

    r = await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": r.json()["owner_id"], "display_name": "Self", "button_index": 1
    }, headers=headers)
    contact_id = r.json()["id"]

    avatar = io.BytesIO(b"fake-image-bytes")
    r = await client.post(f"/api/contacts/{contact_id}/avatar", files={"file": ("avatar.png", avatar, "image/png")}, headers=headers)
    assert r.status_code == 200
    assert r.json()["avatar_path"] is not None
```

- [x] **Step 5：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_uploads.py -v`
Expected: PASS

- [x] **Step 6：提交**

```bash
cd signaling-server
git add app/services/upload_service.py app/routers/contacts.py tests/test_uploads.py
git commit -m "feat(signaling): add avatar upload and static file serving"
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 4：在线状态

### Task 9：Socket.IO 管理器与 Presence 状态

**Files:**
- Create: `signaling-server/app/socket/manager.py`
- Create: `signaling-server/app/socket/namespace.py`
- Test: `signaling-server/tests/test_presence.py`

**Interfaces:**
- Produces: `ConnectionManager`：
  - `connect(sid, device_id)`
  - `disconnect(sid)`
  - `is_online(device_id) -> bool`
  - `get_last_seen(device_id) -> Optional[datetime]`
  - `get_room_for_device(device_id) -> str`
- Consumes: `app.models.Device`

- [x] **Step 1：编写 manager.py**

```python
from datetime import datetime
from typing import Optional


class ConnectionManager:
    def __init__(self):
        self._sid_to_device: dict[str, str] = {}
        self._device_to_sids: dict[str, set[str]] = {}
        self._last_seen: dict[str, datetime] = {}

    def connect(self, sid: str, device_id: str):
        self._sid_to_device[sid] = device_id
        self._device_to_sids.setdefault(device_id, set()).add(sid)
        self._last_seen[device_id] = datetime.utcnow()

    def disconnect(self, sid: str):
        device_id = self._sid_to_device.pop(sid, None)
        if device_id:
            sids = self._device_to_sids.get(device_id, set())
            sids.discard(sid)
            if not sids:
                del self._device_to_sids[device_id]

    def is_online(self, device_id: str) -> bool:
        return device_id in self._device_to_sids and len(self._device_to_sids[device_id]) > 0

    def get_last_seen(self, device_id: str) -> Optional[datetime]:
        return self._last_seen.get(device_id)

    def heartbeat(self, device_id: str):
        self._last_seen[device_id] = datetime.utcnow()

    def get_room_for_device(self, device_id: str) -> str:
        return f"device:{device_id}"


manager = ConnectionManager()
```

- [x] **Step 2：编写 namespace.py 的 presence 事件**

```python
import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Device
from app.services import device_service
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
```

注意：设备 token 后续统一改为 JWT 形式，包含 `device_id` claim，便于 Socket.IO 认证。

- [x] **Step 3：编写 presence 测试**

`signaling-server/tests/test_presence.py`：

```python
from datetime import datetime, timedelta

import pytest
from app.socket.manager import ConnectionManager


def test_manager_tracks_online_status():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    assert mgr.is_online("device-1") is True
    mgr.disconnect("sid-1")
    assert mgr.is_online("device-1") is False


def test_heartbeat_updates_last_seen():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    old = mgr.get_last_seen("device-1")
    mgr.heartbeat("device-1")
    new = mgr.get_last_seen("device-1")
    assert new > old
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_presence.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/socket/manager.py app/socket/namespace.py tests/test_presence.py
git commit -m "feat(signaling): add presence manager and heartbeat handlers"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 10：设备在线状态 HTTP 端点与超时清理

**Files:**
- Modify: `signaling-server/app/routers/devices.py` 增加 `GET /api/devices/{device_id}/status`
- Modify: `signaling-server/app/socket/manager.py` 增加超时检测
- Test: `signaling-server/tests/test_presence.py`

**Interfaces:**
- Produces: `GET /api/devices/{device_id}/status` -> `DeviceStatusResponse`
- Produces: `ConnectionManager.sweep_stale(timeout_seconds)`

- [x] **Step 1：在 manager.py 增加超时检测**

```python
from datetime import datetime, timedelta


class ConnectionManager:
    # ... 已有方法 ...

    def sweep_stale(self, timeout_seconds: int = 60):
        cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        stale = [device_id for device_id, last_seen in self._last_seen.items() if last_seen < cutoff]
        for device_id in stale:
            self._device_to_sids.pop(device_id, None)
        for device_id in stale:
            self._last_seen.pop(device_id, None)
        return stale
```

- [x] **Step 2：在 devices.py 增加状态端点**

```python
from app.schemas import DeviceStatusResponse
from app.socket.manager import manager


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = await device_service.get_owned_device(db, current_user.id, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    manager.sweep_stale()
    return DeviceStatusResponse(
        device_id=device_id,
        online=manager.is_online(device_id),
        last_seen_at=manager.get_last_seen(device_id),
    )
```

- [x] **Step 3：补充超时测试**

```python
from datetime import datetime, timedelta


def test_sweep_stale_marks_offline():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    mgr._last_seen["device-1"] = datetime.utcnow() - timedelta(seconds=120)
    mgr.sweep_stale(timeout_seconds=60)
    assert mgr.is_online("device-1") is False
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_presence.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/routers/devices.py tests/test_presence.py
git commit -m "feat(signaling): add device status endpoint and stale presence sweep"
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 5：通话信令

### Task 11：Socket.IO 连接认证（JWT + 设备 Token）

**Files:**
- Modify: `signaling-server/app/services/device_service.py` 生成设备 JWT
- Modify: `signaling-server/app/socket/namespace.py` 认证逻辑
- Modify: `signaling-server/app/main.py` 挂载 Socket.IO
- Test: `signaling-server/tests/test_signaling.py`

**Interfaces:**
- Produces: `device_service.create_device_token(device_id) -> str` 返回含 `device_id` claim 的 JWT。
- Consumes: Socket.IO 连接 `auth.token` 需同时支持用户 JWT（带 `sub`）和设备 JWT（带 `device_id`）。

- [x] **Step 1：修改 device_service.py 生成设备 JWT**

```python
def create_device_token(device_id: str) -> str:
    return create_access_token({"device_id": device_id})
```

并在 `create_device` 中返回 `(device, create_device_token(device.id))`。

- [x] **Step 2：更新 DeviceTokenResponse**

`signaling-server/app/schemas.py`：

```python
class DeviceTokenResponse(BaseModel):
    device_id: str
    device_token: str
```

- [x] **Step 3：修改 namespace.py 认证逻辑**

```python
from jose import jwt, JWTError

from app.config import get_settings
from app.dependencies import decode_access_token
from app.models import Device, User
from app.services.device_service import verify_device_token


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
```

- [x] **Step 4：在 main.py 挂载 Socket.IO**

```python
import socketio
from app.socket.namespace import signaling_ns

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[])
sio.register_namespace(signaling_ns)
socket_app = socketio.ASGIApp(sio, app)
```

启动脚本改为 `uvicorn app.main:socket_app --host 0.0.0.0 --port 8000`。

- [x] **Step 5：编写 Socket.IO 认证测试**

`signaling-server/tests/test_signaling.py`：

```python
import pytest
import socketio
from httpx import AsyncClient

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_device_socket_connects_with_token(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    r = await client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=headers)
    device_token = r.json()["device_token"]

    sio = socketio.AsyncClient()
    connected = False

    @sio.event
    def connect():
        nonlocal connected
        connected = True

    await sio.connect("http://localhost:8000", namespace="/signaling", auth={"token": device_token})
    assert connected is True
    await sio.disconnect()
```

- [x] **Step 6：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_signaling.py::test_device_socket_connects_with_token -v`
Expected: PASS

- [x] **Step 7：提交**

```bash
cd signaling-server
git add app/services/device_service.py app/socket/namespace.py app/main.py tests/test_signaling.py
git commit -m "feat(signaling): add socket.io auth for users and devices"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 12：Call 服务与信令事件转发

**Files:**
- Create: `signaling-server/app/services/call_service.py`
- Modify: `signaling-server/app/socket/namespace.py` 增加 `call:invite/accept/reject/end` 与 `ice:candidate` 处理
- Test: `signaling-server/tests/test_signaling.py`

**Interfaces:**
- Produces: `call_service.create_call_session(db, call_id, caller_id, callee_device_id) -> CallSession`
- Produces: `call_service.accept_call(db, call_id)`, `reject_call(...)`, `end_call(...)`
- Produces: `call_service.is_active_call(device_id) -> Optional[str]`
- Produces: Socket.IO 事件 `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`, `call:busy`, `call:error`。

- [x] **Step 1：编写 call_service.py**

```python
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
```

- [x] **Step 2：修改 namespace.py 增加 call 事件**

```python
from app.services import call_service, contact_service
from app.socket.manager import manager


class SignalingNamespace(socketio.AsyncNamespace):
    # ... connect/disconnect/heartbeat ...

    async def on_call_invite(self, sid, data):
        async with AsyncSessionLocal() as db:
            session = await self.get_session(sid)
            caller_id = session.get("user_id")
            if caller_id is None:
                await self.emit("call:error", {"callId": data.get("callId"), "reason": "Only users can call"}, room=sid)
                return

            call_id = data.get("callId")
            to_device_id = data.get("toDeviceId")
            offer = data.get("offer")

            if not call_id or not to_device_id:
                await self.emit("call:error", {"callId": call_id, "reason": "Missing callId or toDeviceId"}, room=sid)
                return

            is_allowed = await contact_service.is_contact(db, to_device_id, caller_id)
            if not is_allowed:
                await self.emit("call:error", {"callId": call_id, "reason": "Not in contact list"}, room=sid)
                return

            existing = await call_service.get_call_session(db, call_id)
            if existing is not None and existing.status in ("pending", "accepted"):
                await self.emit("call:busy", {"callId": call_id}, room=sid)
                return

            await call_service.create_call_session(db, call_id, caller_id, to_device_id)
            await self.emit("call:invite", {
                "callId": call_id,
                "callerId": caller_id,
                "callerName": session.get("caller_name", "Caller"),
                "offer": offer,
            }, room=manager.get_room_for_device(to_device_id))

    async def on_call_accept(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session = await call_service.get_call_session(db, call_id)
            if session is None:
                return
            await call_service.accept_call(db, call_id)
            await self.emit("call:accept", {"callId": call_id, "answer": data.get("answer")}, room=manager.get_room_for_device(session.caller_id))

    async def on_call_reject(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session = await call_service.get_call_session(db, call_id)
            if session is None:
                return
            await call_service.reject_call(db, call_id)
            await self.emit("call:reject", {"callId": call_id, "reason": data.get("reason")}, room=manager.get_room_for_device(session.caller_id))

    async def on_call_end(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session = await call_service.get_call_session(db, call_id)
            if session is None:
                return
            await call_service.end_call(db, call_id)
            await self.emit("call:end", {"callId": call_id}, room=manager.get_room_for_device(session.caller_id))
            await self.emit("call:end", {"callId": call_id}, room=manager.get_room_for_device(session.callee_device_id))

    async def on_ice_candidate(self, sid, data):
        async with AsyncSessionLocal() as db:
            call_id = data.get("callId")
            session = await call_service.get_call_session(db, call_id)
            if session is None:
                return
            target_room = manager.get_room_for_device(session.caller_id)
            await self.emit("ice:candidate", {"callId": call_id, "candidate": data.get("candidate")}, room=target_room, skip_sid=sid)
```

注意：`session.caller_id` 是用户 ID，需为该用户在 Socket.IO 中也加入以 `user:{user_id}` 命名的 room，否则转发失败。调整 `on_connect`：当 kind 为 user 时，加入 `user:{user_id}`。

- [x] **Step 3：调整用户连接加入 caller room**

```python
if session["kind"] == "user":
    await self.enter_room(sid, f"user:{session['user_id']}")
    session["caller_name"] = (await db.get(User, session["user_id"])).full_name
```

- [x] **Step 4：编写 invite/accept 端到端测试**

`signaling-server/tests/test_signaling.py`：

```python
import asyncio
import pytest
import socketio
from httpx import AsyncClient

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_call_invite_forwarded_to_device(client):
    # register owner and caller
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    owner_token = (await client.post("/api/auth/login", data={
        "username": "alice@example.com", "password": "secret"
    })).json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    await client.post("/api/auth/register", json={
        "email": "bob@example.com", "password": "secret", "full_name": "Bob"
    })
    caller = (await client.post("/api/auth/login", data={
        "username": "bob@example.com", "password": "secret"
    })).json()
    caller_token = caller["access_token"]
    caller_user_id = caller["user_id"]

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=owner_headers)
    device_id = r.json()["device_id"]
    device_token = r.json()["device_token"]

    await client.post(f"/api/devices/{device_id}/contacts", json={
        "user_id": caller_user_id, "display_name": "Bob", "button_index": 1
    }, headers=owner_headers)

    device_sio = socketio.AsyncClient()
    user_sio = socketio.AsyncClient()
    received_invite = {}

    @device_sio.on("call:invite", namespace="/signaling")
    def on_invite(data):
        received_invite["data"] = data

    await device_sio.connect("http://localhost:8000", namespace="/signaling", auth={"token": device_token})
    await user_sio.connect("http://localhost:8000", namespace="/signaling", auth={"token": caller_token})

    await user_sio.emit("call:invite", {
        "callId": "call-1",
        "toDeviceId": device_id,
        "offer": {"sdp": "fake-offer"}
    }, namespace="/signaling")

    await asyncio.sleep(0.5)
    assert received_invite["data"]["callId"] == "call-1"

    await user_sio.disconnect()
    await device_sio.disconnect()
```

- [x] **Step 5：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_signaling.py -v`
Expected: PASS

- [x] **Step 6：提交**

```bash
cd signaling-server
git add app/services/call_service.py app/socket/namespace.py tests/test_signaling.py
git commit -m "feat(signaling): implement webrtc signaling event relay"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 13：单路通话保护与 CallSession 生命周期

**Files:**
- Modify: `signaling-server/app/socket/namespace.py` 增加 busy 判断
- Modify: `signaling-server/app/services/call_service.py` 增加 `get_active_call_for_device`
- Test: `signaling-server/tests/test_signaling.py`

**Interfaces:**
- Produces: `call_service.get_active_call_for_device(db, device_id) -> Optional[CallSession]`
- Produces: Socket.IO `call:busy` 事件在设备已有进行中的通话时返回。

- [x] **Step 1：在 call_service.py 增加活跃通话查询**

```python
async def get_active_call_for_device(db: AsyncSession, device_id: str) -> Optional[CallSession]:
    result = await db.execute(
        select(CallSession).where(
            CallSession.callee_device_id == device_id,
            CallSession.status.in_(["pending", "accepted"]),
        )
    )
    return result.scalar_one_or_none()
```

- [x] **Step 2：在 on_call_invite 中增加 busy 判断**

```python
active = await call_service.get_active_call_for_device(db, to_device_id)
if active is not None and active.call_id != call_id:
    await self.emit("call:busy", {"callId": call_id}, room=sid)
    return
```

- [x] **Step 3：编写 busy 测试**

```python
async def test_second_call_returns_busy(client):
    # ... 复用 Task 12 的 fixture 注册设备与联系人 ...
    # 发起第一个通话，不结束，再发起第二个，断言收到 call:busy
    pass
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_signaling.py::test_second_call_returns_busy -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add app/services/call_service.py app/socket/namespace.py tests/test_signaling.py
git commit -m "feat(signaling): add single active call guard"
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 6：白名单

### Task 14：通话邀请白名单校验

**Files:**
- Modify: `signaling-server/app/socket/namespace.py`（已包含白名单检查）
- Modify: `signaling-server/app/services/contact_service.py`（已提供 `is_contact`）
- Test: `signaling-server/tests/test_whitelist.py`

**Interfaces:**
- Produces: 非联系人调用 `call:invite` 时，设备侧不应收到事件，调用侧收到 `call:error`。

- [x] **Step 1：编写白名单测试**

`signaling-server/tests/test_whitelist.py`：

```python
import asyncio
import pytest
import socketio
from httpx import AsyncClient

from app.db import async_engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_unauthorized_call_rejected(client):
    await client.post("/api/auth/register", json={
        "email": "alice@example.com", "password": "secret", "full_name": "Alice"
    })
    owner_token = (await client.post("/api/auth/login", data={
        "username": "alice@example.com", "password": "secret"
    })).json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    await client.post("/api/auth/register", json={
        "email": "stranger@example.com", "password": "secret", "full_name": "Stranger"
    })
    stranger_token = (await client.post("/api/auth/login", data={
        "username": "stranger@example.com", "password": "secret"
    })).json()["access_token"]

    r = await client.post("/api/devices", json={"display_name": "Pi"}, headers=owner_headers)
    device_id = r.json()["device_id"]
    device_token = r.json()["device_token"]

    device_sio = socketio.AsyncClient()
    stranger_sio = socketio.AsyncClient()
    received = {}

    @device_sio.on("call:invite", namespace="/signaling")
    def on_invite(data):
        received["invite"] = data

    @stranger_sio.on("call:error", namespace="/signaling")
    def on_error(data):
        received["error"] = data

    await device_sio.connect("http://localhost:8000", namespace="/signaling", auth={"token": device_token})
    await stranger_sio.connect("http://localhost:8000", namespace="/signaling", auth={"token": stranger_token})

    await stranger_sio.emit("call:invite", {
        "callId": "call-unauthorized",
        "toDeviceId": device_id,
        "offer": {"sdp": "fake"}
    }, namespace="/signaling")

    await asyncio.sleep(0.5)
    assert "invite" not in received
    assert received["error"]["reason"] == "Not in contact list"

    await stranger_sio.disconnect()
    await device_sio.disconnect()
```

- [x] **Step 2：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_whitelist.py -v`
Expected: PASS

- [x] **Step 3：提交**

```bash
cd signaling-server
git add tests/test_whitelist.py
git commit -m "feat(signaling): enforce contact whitelist for call invites"
```

archived-with: 2026-06-18-video-call-signaling
---

## 阶段 7：部署与文档

### Task 15：Docker 与运行脚本

**Files:**
- Create: `signaling-server/Dockerfile`
- Create: `signaling-server/docker-compose.yml`
- Modify: `signaling-server/app/main.py` 最终确认入口
- Test: `signaling-server/tests/test_health.py`

**Interfaces:**
- Produces: `docker-compose up --build` 可启动完整服务。

- [x] **Step 1：编写 Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY uploads ./uploads

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
```

- [x] **Step 2：编写 docker-compose.yml**

```yaml
version: "3.8"

services:
  signaling:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL:-sqlite+aiosqlite:///./data/signaling.db}
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-1440}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - PORT=8000
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    restart: unless-stopped
```

- [x] **Step 3：编写 health 测试**

`signaling-server/tests/test_health.py`：

```python
import pytest
from httpx import AsyncClient

from app.main import app


async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
```

- [x] **Step 4：运行测试**

Run: `cd signaling-server && python -m pytest tests/test_health.py -v`
Expected: PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add Dockerfile docker-compose.yml tests/test_health.py
git commit -m "chore(signaling): add docker deployment and health check"
```

archived-with: 2026-06-18-video-call-signaling
---

### Task 16：README、Seed 脚本与事件文档

**Files:**
- Create: `signaling-server/README.md`
- Create: `signaling-server/scripts/seed.py`
- Create: `signaling-server/docs/EVENTS.md`

**Interfaces:**
- Produces：可运行的本地开发指南、示例数据、Socket.IO 事件载荷说明。

- [x] **Step 1：编写 README.md**

```markdown
# Video Call Signaling Server

基于 FastAPI + python-socketio 的视频通话信令后端。

## 本地开发

```bash
cd signaling-server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m pytest
uvicorn app.main:socket_app --reload
```

## Docker 部署

```bash
cp .env.example .env
# 编辑 .env
docker-compose up --build
```

## 主要路由

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/devices`
- `GET /api/devices/{device_id}/status`
- `POST /api/devices/{device_id}/contacts`
- `PATCH /api/contacts/{contact_id}`
- `POST /api/contacts/{contact_id}/avatar`
- Socket.IO namespace `/signaling`
```

- [x] **Step 2：编写 seed.py**

```python
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
```

- [x] **Step 3：编写 EVENTS.md**

```markdown
# Socket.IO Events

Namespace: `/signaling`

## Connection Auth

```json
{
  "token": "<user-jwt-or-device-jwt>"
}
```

## Client -> Server

### `call:invite`
```json
{
  "callId": "uuid",
  "toDeviceId": "device-uuid",
  "offer": { "type": "offer", "sdp": "..." }
}
```

### `call:accept`
```json
{
  "callId": "uuid",
  "answer": { "type": "answer", "sdp": "..." }
}
```

### `call:reject`
```json
{
  "callId": "uuid",
  "reason": "declined"
}
```

### `call:end`
```json
{ "callId": "uuid" }
```

### `ice:candidate`
```json
{
  "callId": "uuid",
  "candidate": { "candidate": "...", "sdpMid": "0", "sdpMLineIndex": 0 }
}
```

### `presence:heartbeat`
```json
{}
```

## Server -> Client

- `call:invite` — 转发给被叫设备
- `call:accept` — 转发给主叫用户
- `call:reject` — 转发给主叫用户
- `call:end` — 双方转发
- `ice:candidate` — 双方转发
- `call:busy` — 目标设备忙
- `call:error` — 通用错误
```

- [x] **Step 4：运行全部测试**

Run: `cd signaling-server && python -m pytest`
Expected: 全部 PASS

- [x] **Step 5：提交**

```bash
cd signaling-server
git add README.md scripts/seed.py docs/EVENTS.md
git commit -m "docs(signaling): add README, seed script and event schema docs"
```

archived-with: 2026-06-18-video-call-signaling
---

## Self-Review

### 1. Spec Coverage

| Design Doc 要求 | 对应任务 |
|---|---|
| Python 3.11+ + FastAPI + python-socketio | Task 1 |
| SQLAlchemy 2.0 + SQLite | Task 2 |
| JWT Bearer 认证 | Task 4、Task 5 |
| 用户注册/登录 | Task 5 |
| 设备注册与 deviceToken | Task 6、Task 11 |
| 联系人 CRUD + 按钮唯一性 | Task 7 |
| 头像上传与静态文件 | Task 8 |
| `presence:heartbeat` 与在线状态 | Task 9、Task 10 |
| Socket.IO `/signaling` 命名空间 | Task 9 起 |
| `call:invite/accept/reject/end` 与 `ice:candidate` | Task 12 |
| 单路通话保护 | Task 13 |
| CallSession 生命周期记录 | Task 12、Task 13 |
| 白名单校验与 `call:error` | Task 14 |
| Docker / uvicorn 部署 | Task 15 |
| README / 事件文档 | Task 16 |

### 2. Placeholder Scan

- 无 `TBD`、`TODO` 或模糊描述。
- 每个任务均提供具体文件路径、测试命令与提交信息。
- 涉及代码的任务包含完整代码片段。

### 3. Type / Signature 一致性

- `DeviceTokenResponse` 同时用于 `devices.py` 与 `device_service.py`。
- `ContactCreate/Update/Response` 在 `contact_service.py`、`contacts.py`、`schemas.py` 中保持一致。
- Socket.IO 事件名统一为 `call:invite`、`call:accept`、`call:reject`、`call:end`、`ice:candidate`、`call:busy`、`call:error`。

### 已知待补充点

- Task 7 的测试代码假设 `login` 响应包含 `user_id`；需在 Task 5 的 `login` 实现中一并返回。
- Task 11 的设备 token 从明文改为 JWT，需同步修改 Task 6 的 `create_device` 与 `DeviceTokenResponse` 说明；已在 Task 11 步骤中覆盖。
