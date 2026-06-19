import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")  # active / completed / timeout / error
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    turns = relationship("VoiceTurn", back_populates="session", cascade="all, delete-orphan")


class VoiceTurn(Base):
    __tablename__ = "voice_turns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("voice_sessions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant
    audio_url = Column(String(500), nullable=True)
    text = Column(Text, nullable=True)
    intent = Column(String(20), nullable=True)  # call / message / check_messages / unknown
    intent_data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("VoiceSession", back_populates="turns")


class VoiceMessage(Base):
    __tablename__ = "voice_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sender_device_id = Column(String(36), nullable=False, index=True)
    recipient_device_id = Column(String(36), nullable=False, index=True)
    audio_url = Column(String(500), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="unread")  # unread / read
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)


class MessageNotification(Base):
    __tablename__ = "message_notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), nullable=False, index=True)
    message_id = Column(String(36), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending / delivered / acknowledged
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
