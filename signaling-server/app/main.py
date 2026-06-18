from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount

from app.config import get_settings
from app.routers import auth, devices
from app.routers.contacts import api_router as contacts_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    fresh_settings = get_settings()
    upload_dir = Path(fresh_settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    if not any(isinstance(route, Mount) and route.path == "/uploads" for route in app.routes):
        app.mount("/uploads", StaticFiles(directory=fresh_settings.upload_dir), name="uploads")
    yield


app = FastAPI(title="Video Call Signaling Server", lifespan=lifespan)

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


@app.get("/health")
async def health():
    return {"status": "ok"}
