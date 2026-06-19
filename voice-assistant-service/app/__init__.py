from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import engine, Base
from app.routers import sessions, messages
from app.websocket import voice_ws_router

app = FastAPI(
    title="Voice Assistant Service",
    description="AI-powered voice assistant for elder-pi",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(sessions.router, prefix="/api/voice", tags=["voice"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(voice_ws_router, prefix="/ws")


@app.get("/health")
async def health():
    return {"status": "ok"}
