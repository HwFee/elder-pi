from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.dialog import DialogEngine

router = APIRouter()


@router.post("/sessions")
async def create_session(device_id: str, db: Session = Depends(get_db)):
    """创建新的语音对话会话"""
    pass


@router.post("/sessions/{session_id}/audio")
async def upload_audio(
    session_id: str,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传语音文件，返回理解和下一步动作"""
    pass
