from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter()


@router.get("/")
async def get_messages(
    device_id: str = Query(...),
    status: str = Query("unread"),
    db: Session = Depends(get_db),
):
    """获取消息列表"""
    pass


@router.post("/{message_id}/read")
async def mark_read(message_id: str, db: Session = Depends(get_db)):
    """标记消息为已读"""
    pass


@router.post("/")
async def send_message(db: Session = Depends(get_db)):
    """发送语音消息（内部调用）"""
    pass
