from fastapi import APIRouter, WebSocket, WebSocketDisconnect

voice_ws_router = APIRouter()


@voice_ws_router.websocket("/voice/{device_id}")
async def voice_websocket(websocket: WebSocket, device_id: str):
    """WebSocket 连接，实时语音交互"""
    await websocket.accept()
    try:
        while True:
            # 接收音频数据或控制指令
            data = await websocket.receive()
            # TODO: 处理音频数据，调用 STT/AI/TTS，返回结果
            pass
    except WebSocketDisconnect:
        pass
