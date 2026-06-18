from contextlib import asynccontextmanager
from pathlib import Path

import asyncio
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import auth, devices
from app.routers.contacts import api_router as contacts_router
from app.socket.manager import manager
from app.socket.namespace import signaling_ns

settings = get_settings()


class UploadStaticFiles(StaticFiles):
    def __init__(self):
        super().__init__(directory=settings.upload_dir, check_dir=False)

    async def __call__(self, scope, receive, send):
        self.directory = get_settings().upload_dir
        self.all_directories = self.get_directories(self.directory, self.packages)
        self.config_checked = False
        await super().__call__(scope, receive, send)


async def _presence_sweep_loop(interval_seconds: int = 60):
    while True:
        await asyncio.sleep(interval_seconds)
        manager.sweep_stale(timeout_seconds=interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    sweep_task = asyncio.create_task(_presence_sweep_loop())
    try:
        yield
    finally:
        sweep_task.cancel()
        try:
            await sweep_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Video Call Signaling Server", lifespan=lifespan)
app.mount("/uploads", UploadStaticFiles(), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["contacts"])


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.cors_origins)
sio.register_namespace(signaling_ns)
socket_app = socketio.ASGIApp(sio, app)
