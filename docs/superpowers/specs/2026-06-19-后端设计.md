# voice-assistant-service 后端设计文档

**日期**: 2026-06-19  
**服务**: voice-assistant-service  
**目标**: 为 elder-pi 提供 AI 语音助手能力（打电话 + 发消息）

---

## 1. 技术栈

| 组件 | 选型 | 版本 |
|------|------|------|
| 框架 | FastAPI | ^0.104 |
| ORM | SQLAlchemy | ^2.0 |
| 配置 | Pydantic Settings | ^2.0 |
| HTTP 客户端 | httpx | ^0.25 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | - |
| Python | 3.11+ | - |

---

## 2. 目录结构

```
voice-assistant-service/
├── app/
│   ├── __init__.py          # FastAPI 应用实例
│   ├── main.py              # 启动入口 (uvicorn app.main:app)
│   ├── config.py            # Settings 配置类
│   ├── db.py                # Engine + SessionLocal + Base + get_db
│   ├── models.py            # SQLAlchemy 模型 (4张表)
│   ├── websocket.py         # WebSocket 语音连接处理
│   ├── prompts/
│   │   ├── system.txt       # 意图识别 Prompt 模板
│   │   └── confirm.txt      # 确认语生成 Prompt 模板
│   ├── routers/
│   │   ├── sessions.py      # 会话管理 API
│   │   └── messages.py      # 消息管理 API
│   └── services/
│       ├── stt.py           # 语音识别服务
│       ├── llm.py           # 大模型服务
│       ├── tts.py           # 语音合成服务
│       ├── dialog.py        # 对话引擎 (核心逻辑)
│       └── signaling_client.py  # signaling-server 内部 API 客户端
├── tests/
├── uploads/                 # 语音文件存储目录 (gitignore)
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. 数据模型详解

### 3.1 voice_sessions (对话会话)

一次"按按钮 → 交互 → 结束"的完整生命周期。

```python
class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")
    # active: 进行中
    # completed: 正常完成
    # timeout: 超时结束
    # error: 异常结束
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    turns = relationship("VoiceTurn", back_populates="session", cascade="all, delete-orphan", order_by="VoiceTurn.turn_number")
```

**生命周期**:
1. 老人按按钮 → 创建 session，status="active"
2. 每轮对话创建 VoiceTurn
3. 完成/超时/错误 → 更新 status，设置 ended_at

### 3.2 voice_turns (对话轮次)

记录每轮对话，用于调试和 AI 上下文。

```python
class VoiceTurn(Base):
    __tablename__ = "voice_turns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("voice_sessions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)  # 从 1 开始递增
    role = Column(String(20), nullable=False)  # user:老人, assistant:AI
    audio_url = Column(String(500), nullable=True)  # 老人录音文件路径
    text = Column(Text, nullable=True)  # STT 转写文字
    intent = Column(String(20), nullable=True)  # call/message/check_messages/unknown
    intent_data = Column(Text, nullable=True)  # JSON: {"target":"张三","content":"..."}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("VoiceSession", back_populates="turns")
```

**典型记录**:

| turn | role | text | intent | intent_data |
|------|------|------|--------|-------------|
| 1 | user | "给张三打电话" | call | `{"target":"张三","target_device_id":"xxx"}` |
| 2 | assistant | "您要打电话给张三吗？请说确认或取消。" | confirm | `{"action":"call","details":"张三"}` |
| 3 | user | "确认" | call | `{"target":"张三","target_device_id":"xxx","confirmed":true}` |
| 4 | assistant | "正在为您拨号..." | system | `{"action":"initiate_call"}` |

### 3.3 voice_messages (语音消息)

```python
class VoiceMessage(Base):
    __tablename__ = "voice_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sender_device_id = Column(String(36), nullable=False, index=True)
    recipient_device_id = Column(String(36), nullable=False, index=True)
    audio_url = Column(String(500), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="unread")  # unread/read
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
```

### 3.4 message_notifications (消息通知)

```python
class MessageNotification(Base):
    __tablename__ = "message_notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), nullable=False, index=True)
    message_id = Column(String(36), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    # pending: 待推送
    # delivered: 已推送到设备
    # acknowledged: 设备已确认收到
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

---

## 4. API 详解

### 4.1 WebSocket 连接 (核心)

```
WS /ws/voice/{device_id}
```

**连接建立**:
```json
// 客户端 → 服务端: 连接时发送 device_token 认证
{
  "type": "auth",
  "token": "Bearer xxx"
}

// 服务端 → 客户端: 认证成功
{
  "type": "auth_success",
  "session_id": "xxx"  // 可选，复用已有 session
}
```

**音频上传**:
```json
// 客户端 → 服务端: 上传音频 (二进制帧，或 base64 JSON)
{
  "type": "audio",
  "format": "webm/opus",
  "data": "base64..."  // 或直接用二进制帧
}

// 服务端 → 客户端: 处理结果
{
  "type": "response",
  "action": "confirm",  // confirm/execute/ask/clarify/play_messages/error
  "text": "您要打电话给张三吗？请说确认或取消。",
  "audio_url": "/tts/xxx.wav",  // TTS 音频 URL
  "data": {
    "intent": "call",
    "target": "张三",
    "target_device_id": "xxx"
  }
}
```

**控制指令**:
```json
// 服务端 → 客户端: 执行打电话
{
  "type": "command",
  "action": "initiate_call",
  "data": {
    "call_id": "xxx",
    "target_device_id": "xxx",
    "target_name": "张三"
  }
}

// 服务端 → 客户端: 播放消息
{
  "type": "command",
  "action": "play_messages",
  "data": {
    "messages": [
      {"id": "xxx", "audio_url": "/uploads/xxx.wav", "sender_name": "李四"}
    ]
  }
}
```

**心跳**:
```json
// 双向 ping/pong
{"type": "ping"}
{"type": "pong"}
```

### 4.2 HTTP API

#### POST /api/voice/sessions
创建新对话会话。

**请求**:
```json
{
  "device_id": "xxx"
}
```

**响应**:
```json
{
  "session_id": "xxx",
  "status": "active",
  "created_at": "2026-06-19T10:00:00Z"
}
```

#### POST /api/voice/sessions/{session_id}/audio
上传语音文件，返回 AI 理解和下一步动作。

**请求**: `multipart/form-data`
- `audio`: 音频文件 (webm/opus, max 10MB)
- `turn_number`: 轮次编号 (可选，默认自动递增)

**响应**:
```json
{
  "turn_id": "xxx",
  "text": "给张三打电话",
  "intent": "call",
  "intent_data": {
    "target": "张三",
    "target_device_id": "xxx",
    "confidence": 0.95
  },
  "next_action": "confirm",
  "response_text": "您要打电话给张三吗？请说确认或取消。",
  "response_audio_url": "/tts/xxx.wav"
}
```

#### GET /api/messages
获取消息列表。

**参数**:
- `device_id` (required): 设备 ID
- `status` (optional): `unread` | `read` | `all`, 默认 `all`
- `limit` (optional): 数量, 默认 50
- `offset` (optional): 偏移, 默认 0

**响应**:
```json
{
  "total": 10,
  "messages": [
    {
      "id": "xxx",
      "sender_device_id": "xxx",
      "sender_name": "李四",
      "audio_url": "/uploads/xxx.wav",
      "duration_ms": 32000,
      "status": "unread",
      "created_at": "2026-06-19T10:00:00Z"
    }
  ]
}
```

#### POST /api/messages/{message_id}/read
标记消息为已读。

**响应**: `204 No Content`

#### POST /api/messages
发送语音消息（内部 API，AI 决定发消息时调用）。

**请求**:
```json
{
  "sender_device_id": "xxx",
  "recipient_device_id": "xxx",
  "audio_url": "/uploads/xxx.wav",
  "duration_ms": 15000
}
```

**响应**:
```json
{
  "id": "xxx",
  "status": "sent",
  "created_at": "2026-06-19T10:00:00Z"
}
```

---

## 5. 服务层设计

### 5.1 STTService (app/services/stt.py)

```python
class STTService:
    """语音识别服务封装"""
    
    def __init__(self, api_key: str, api_url: str = None):
        self.api_key = api_key
        self.api_url = api_url or "https://api.xxx.com/stt"
    
    async def transcribe(self, audio_path: str) -> str:
        """
        将语音文件转为文字。
        
        Args:
            audio_path: 本地音频文件路径
            
        Returns:
            转写后的文字
            
        Raises:
            STTException: 识别失败
        """
        # 1. 读取音频文件
        # 2. 调用云端 STT API (如讯飞、阿里云)
        # 3. 返回文字结果
        pass
    
    async def transcribe_stream(self, audio_stream: bytes) -> str:
        """流式识别（WebSocket 实时场景）"""
        pass
```

**实现要点**:
- 支持常见格式: webm, wav, mp3, m4a
- 超过 60 秒音频分片处理
- 错误重试: 最多 3 次，指数退避
- 超时: 30 秒

### 5.2 LLMService (app/services/llm.py)

```python
class LLMService:
    """大模型服务封装"""
    
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    async def understand(
        self, 
        text: str, 
        contacts: list[dict], 
        context: list[dict] = None
    ) -> dict:
        """
        理解用户意图。
        
        Args:
            text: STT 转写文字
            contacts: 可用联系人列表 [{"name": "张三", "device_id": "xxx"}]
            context: 前几轮对话历史 [{"role": "user", "text": "..."}, ...]
            
        Returns:
            {
                "intent": "call" | "message" | "check_messages" | "unknown",
                "target": "张三" | null,
                "target_device_id": "xxx" | null,
                "content": "消息内容" | null,
                "confidence": 0.95,
                "needs_clarification": false,
                "clarification_question": null
            }
        """
        # 1. 读取 system.txt prompt
        # 2. 格式化 contacts 为 JSON
        # 3. 构建 messages: system + context + user
        # 4. 调用大模型 API
        # 5. 解析 JSON 响应
        # 6. 联系人模糊匹配 (如 "老张" -> "张三")
        pass
    
    async def generate_confirm(self, action: str, details: str) -> str:
        """
        生成确认语句。
        
        Args:
            action: "call" | "message"
            details: 动作详情，如 "打电话给张三" 或 "给李四发消息：我明天去公园"
            
        Returns:
            确认语句，如 "您要打电话给张三吗？请说确认或取消。"
        """
        # 1. 读取 confirm.txt prompt
        # 2. 格式化模板
        # 3. 调用大模型生成
        # 4. 或直接拼接模板（更可控）
        pass
```

**实现要点**:
- Prompt 模板放在 `app/prompts/` 目录，运行时读取
- 联系人匹配用模糊匹配 (fuzzywuzzy 或 difflib)
- 大模型响应必须是合法 JSON，失败时 fallback 到 unknown
- 上下文只保留最近 5 轮，避免 token 超限

### 5.3 TTSService (app/services/tts.py)

```python
class TTSService:
    """语音合成服务封装"""
    
    def __init__(self, api_key: str, voice: str = "xiaoyan"):
        self.api_key = api_key
        self.voice = voice  # 音色
    
    async def synthesize(self, text: str) -> str:
        """
        将文字转为语音。
        
        Args:
            text: 要合成的文字
            
        Returns:
            本地音频文件路径，如 "/uploads/tts/xxx.wav"
        """
        # 1. 调用云端 TTS API
        # 2. 保存到 uploads/tts/ 目录
        # 3. 返回文件路径
        pass
    
    async def synthesize_to_bytes(self, text: str) -> bytes:
        """合成后直接返回字节（WebSocket 场景）"""
        pass
```

**实现要点**:
- 音色选择: 温暖、清晰、适合老人的声音
- 语速: 偏慢 (如 0.8x)
- 缓存: 相同文字直接复用已生成音频
- 文件命名: md5(text) + ".wav"

### 5.4 DialogEngine (app/services/dialog.py)

**核心逻辑，串联所有服务**。

```python
class DialogEngine:
    """对话管理引擎"""
    
    def __init__(
        self,
        stt: STTService,
        llm: LLMService,
        tts: TTSService,
        signaling: SignalingClient,
        db: Session,
    ):
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.signaling = signaling
        self.db = db
    
    async def process_turn(self, session_id: str, audio_path: str) -> dict:
        """
        处理一轮对话。核心方法。
        
        流程:
        1. STT 转写
        2. 获取联系人列表
        3. LLM 理解意图
        4. 根据意图和完整度决定下一步
        5. 生成 TTS 回复
        6. 保存对话记录
        7. 返回结果
        
        Returns:
            {
                "next_action": "confirm" | "execute" | "ask" | "clarify" | "play_messages" | "error",
                "response_text": "AI 回复文字",
                "response_audio_url": "/tts/xxx.wav",
                "data": {...}  // 意图数据
            }
        """
        pass
    
    async def _handle_call_intent(self, intent_data: dict, session: VoiceSession) -> dict:
        """处理打电话意图"""
        # 1. 确认 target_device_id 存在
        # 2. 如果已确认，调用 signaling 发起通话
        # 3. 如果未确认，生成确认语
        pass
    
    async def _handle_message_intent(self, intent_data: dict, session: VoiceSession) -> dict:
        """处理发消息意图"""
        # 1. 确认 target_device_id 和 content 存在
        # 2. 如果已确认，保存消息并通知
        # 3. 如果未确认，生成确认语
        pass
    
    async def _handle_check_messages(self, device_id: str) -> dict:
        """处理查消息意图"""
        # 1. 查询未读消息
        # 2. 生成 TTS: "您有 X 条新消息"
        # 3. 返回 play_messages 指令
        pass
    
    async def check_messages(self, device_id: str) -> list[VoiceMessage]:
        """查询未读消息"""
        pass
    
    async def create_session(self, device_id: str) -> VoiceSession:
        """创建新会话"""
        pass
    
    async def end_session(self, session_id: str, status: str = "completed"):
        """结束会话"""
        pass
```

**状态机**:

```
[开始] → 录音中 → STT处理中 → AI理解中
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          [信息完整]      [信息不完整]      [意图=查消息]
              │               │               │
              ▼               ▼               ▼
          [待确认] → 用户说"确认" → [执行]
              │                    │
              └─ 用户说"取消" ─────┘→ [取消]
```

### 5.5 SignalingClient (app/services/signaling_client.py)

```python
class SignalingClient:
    """调用 signaling-server 内部 API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Internal-API-Key": api_key}
    
    async def get_contacts(self, device_id: str) -> list[dict]:
        """
        获取设备联系人列表。
        
        Returns:
            [{"user_id": "xxx", "display_name": "张三", "device_id": "xxx"}]
        """
        pass
    
    async def initiate_call(
        self, 
        call_id: str, 
        caller_device_id: str, 
        callee_device_id: str, 
        offer: dict
    ) -> dict:
        """
        发起通话。
        
        Args:
            call_id: 通话 ID
            caller_device_id: 主叫设备
            callee_device_id: 被叫设备
            offer: WebRTC offer SDP
            
        Returns:
            {"status": "pending" | "busy" | "offline"}
        """
        pass
    
    async def get_device_info(self, device_id: str) -> dict:
        """获取设备信息（用于验证设备存在）"""
        pass
```

**实现要点**:
- 使用 `httpx.AsyncClient` 保持连接池
- 超时: 5 秒
- 错误处理: signaling-server 不可用时返回友好错误
- 认证: `X-Internal-API-Key` header

---

## 6. WebSocket 实现细节

### 6.1 连接管理

```python
# app/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

# 全局连接管理器
class ConnectionManager:
    def __init__(self):
        # device_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        # 断开旧连接（同一设备只能有一个连接）
        if device_id in self.active_connections:
            old_ws = self.active_connections[device_id]
            if old_ws.client_state != WebSocketState.DISCONNECTED:
                await old_ws.close()
        self.active_connections[device_id] = websocket
    
    def disconnect(self, device_id: str):
        self.active_connections.pop(device_id, None)
    
    async def send_to_device(self, device_id: str, message: dict):
        if device_id in self.active_connections:
            ws = self.active_connections[device_id]
            if ws.client_state != WebSocketState.DISCONNECTED:
                await ws.send_json(message)
    
    async def broadcast(self, message: dict):
        for ws in self.active_connections.values():
            if ws.client_state != WebSocketState.DISCONNECTED:
                await ws.send_json(message)

manager = ConnectionManager()
```

### 6.2 消息处理循环

```python
@voice_ws_router.websocket("/voice/{device_id}")
async def voice_websocket(websocket: WebSocket, device_id: str):
    await manager.connect(device_id, websocket)
    
    try:
        while True:
            raw_data = await websocket.receive()
            
            if "text" in raw_data:
                # JSON 控制消息
                msg = json.loads(raw_data["text"])
                await handle_json_message(device_id, msg, websocket)
            elif "bytes" in raw_data:
                # 二进制音频数据
                await handle_audio_data(device_id, raw_data["bytes"], websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(device_id)
    except Exception as e:
        logger.error(f"WebSocket error for {device_id}: {e}")
        manager.disconnect(device_id)


async def handle_json_message(device_id: str, msg: dict, websocket: WebSocket):
    msg_type = msg.get("type")
    
    if msg_type == "auth":
        # 验证 token
        token = msg.get("token", "")
        # TODO: 验证 JWT
        await websocket.send_json({"type": "auth_success"})
    
    elif msg_type == "start_session":
        # 创建新会话
        session = await dialog_engine.create_session(device_id)
        await websocket.send_json({
            "type": "session_started",
            "session_id": session.id
        })
    
    elif msg_type == "end_session":
        session_id = msg.get("session_id")
        await dialog_engine.end_session(session_id, "completed")
        await websocket.send_json({"type": "session_ended"})
    
    elif msg_type == "ping":
        await websocket.send_json({"type": "pong"})


async def handle_audio_data(device_id: str, audio_bytes: bytes, websocket: WebSocket):
    # 1. 保存音频到临时文件
    temp_path = f"uploads/temp/{device_id}_{uuid.uuid4()}.webm"
    with open(temp_path, "wb") as f:
        f.write(audio_bytes)
    
    # 2. 获取当前会话
    session = await get_active_session(device_id)
    if not session:
        await websocket.send_json({
            "type": "error",
            "message": "没有活跃的会话，请先按按钮"
        })
        return
    
    # 3. 调用 DialogEngine 处理
    result = await dialog_engine.process_turn(session.id, temp_path)
    
    # 4. 发送结果
    await websocket.send_json({
        "type": "response",
        **result
    })
    
    # 5. 如果 action 是 execute，发送执行指令
    if result["next_action"] == "execute":
        if result["data"]["intent"] == "call":
            await websocket.send_json({
                "type": "command",
                "action": "initiate_call",
                "data": result["data"]
            })
        elif result["data"]["intent"] == "message":
            await websocket.send_json({
                "type": "command",
                "action": "message_sent",
                "data": result["data"]
            })
```

### 6.3 超时检测

```python
async def session_timeout_watcher(session_id: str, device_id: str):
    """后台任务：检测会话超时"""
    timeout = 20  # 20 秒无响应则超时
    
    await asyncio.sleep(timeout)
    
    session = await get_session(session_id)
    if session and session.status == "active":
        # 检查最后活动时间
        last_turn = get_last_turn(session_id)
        if last_turn and (datetime.utcnow() - last_turn.created_at).seconds > timeout:
            # 超时，结束会话
            await dialog_engine.end_session(session_id, "timeout")
            await manager.send_to_device(device_id, {
                "type": "response",
                "next_action": "error",
                "response_text": "操作已超时，请重新按按钮",
                "response_audio_url": "/tts/timeout.wav"
            })
```

---

## 7. 文件上传处理

### 7.1 音频文件存储

```
uploads/
├── temp/           # 临时文件，定期清理
├── tts/            # TTS 生成的音频，可缓存
└── messages/       # 语音消息，按日期分目录
    ├── 2026-06-19/
    │   ├── xxx.webm
    │   └── yyy.webm
```

### 7.2 上传限制

```python
# app/routers/sessions.py

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FORMATS = ["audio/webm", "audio/wav", "audio/mp3", "audio/m4a"]

async def upload_audio(
    session_id: str,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. 验证文件类型
    if audio.content_type not in ALLOWED_FORMATS:
        raise HTTPException(400, "不支持的音频格式")
    
    # 2. 验证文件大小
    content = await audio.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(400, "音频文件过大，最大 10MB")
    
    # 3. 保存文件
    ext = audio.filename.split(".")[-1] if "." in audio.filename else "webm"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"uploads/temp/{filename}"
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 4. 处理...
```

---

## 8. 配置管理

### 8.1 .env 配置

```bash
# 数据库
DATABASE_URL=sqlite:///./voice-assistant.db

# API 密钥 (必填)
STT_API_KEY=your_stt_api_key_here
LLM_API_KEY=your_llm_api_key_here
TTS_API_KEY=your_tts_api_key_here

# 信令服务器
SIGNALING_SERVER_URL=http://localhost:8000
SIGNALING_API_KEY=your_internal_api_key_here

# 文件上传
UPLOAD_DIR=./uploads
MAX_AUDIO_SIZE_MB=10

# LLM 配置
LLM_MODEL=qwen-turbo        # 或其他模型
LLM_TEMPERATURE=0.3         # 低温度，输出更确定
LLM_MAX_TOKENS=512

# TTS 配置
TTS_VOICE=xiaoyan           # 音色
TTS_SPEED=0.8               # 语速

# 超时配置
SESSION_TIMEOUT_SECONDS=20    # 会话超时
STT_TIMEOUT_SECONDS=30        # STT 调用超时
LLM_TIMEOUT_SECONDS=10        # LLM 调用超时
TTS_TIMEOUT_SECONDS=15        # TTS 调用超时

# 日志
LOG_LEVEL=INFO
```

### 8.2 config.py 实现

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite:///./voice-assistant.db"
    cors_origins: List[str] = ["*"]
    
    # API Keys
    stt_api_key: str = ""
    stt_api_url: str = "https://api.xxx.com/stt"
    llm_api_key: str = ""
    llm_api_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    llm_model: str = "qwen-turbo"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 512
    tts_api_key: str = ""
    tts_api_url: str = "https://api.xxx.com/tts"
    tts_voice: str = "xiaoyan"
    tts_speed: float = 0.8
    
    # Signaling Server
    signaling_server_url: str = "http://localhost:8000"
    signaling_api_key: str = ""
    
    # Upload
    upload_dir: str = "./uploads"
    max_audio_size_mb: int = 10
    
    # Timeouts
    session_timeout_seconds: int = 20
    stt_timeout_seconds: int = 30
    llm_timeout_seconds: int = 10
    tts_timeout_seconds: int = 15
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## 9. 异常处理

### 9.1 自定义异常

```python
# app/exceptions.py (新建)

class VoiceAssistantException(Exception):
    """基础异常"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class STTException(VoiceAssistantException):
    """语音识别失败"""
    pass


class LLMException(VoiceAssistantException):
    """大模型调用失败"""
    pass


class TTSException(VoiceAssistantException):
    """语音合成失败"""
    pass


class SignalingException(VoiceAssistantException):
    """信令服务器调用失败"""
    pass


class ValidationException(VoiceAssistantException):
    """输入验证失败"""
    pass
```

### 9.2 全局异常处理器

```python
# app/main.py

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(VoiceAssistantException)
async def voice_assistant_exception_handler(request: Request, exc: VoiceAssistantException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.code or "VOICE_ASSISTANT_ERROR",
            "message": exc.message
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "系统繁忙，请稍后再试"
        }
    )
```

---

## 10. 测试策略

### 10.1 单元测试

```python
# tests/test_stt.py
import pytest
from app.services.stt import STTService

@pytest.mark.asyncio
async def test_stt_transcribe():
    stt = STTService(api_key="test-key")
    # Mock API 响应
    result = await stt.transcribe("tests/fixtures/hello.webm")
    assert isinstance(result, str)
    assert len(result) > 0


# tests/test_llm.py
@pytest.mark.asyncio
async def test_llm_understand_call():
    llm = LLMService(api_key="test-key")
    contacts = [{"name": "张三", "device_id": "xxx"}]
    result = await llm.understand("给张三打电话", contacts)
    assert result["intent"] == "call"
    assert result["target"] == "张三"


# tests/test_dialog.py
@pytest.mark.asyncio
async def test_dialog_process_turn():
    # Mock 所有依赖
    dialog = DialogEngine(...)
    result = await dialog.process_turn("session-id", "audio-path")
    assert "next_action" in result
```

### 10.2 集成测试

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_session():
    response = client.post("/api/voice/sessions", json={"device_id": "test-device"})
    assert response.status_code == 200
    assert "session_id" in response.json()

def test_upload_audio():
    # 先创建会话
    session = client.post("/api/voice/sessions", json={"device_id": "test-device"}).json()
    
    # 上传音频
    with open("tests/fixtures/hello.webm", "rb") as f:
        response = client.post(
            f"/api/voice/sessions/{session['session_id']}/audio",
            files={"audio": ("hello.webm", f, "audio/webm")}
        )
    assert response.status_code == 200
    assert "intent" in response.json()
```

### 10.3 WebSocket 测试

```python
# tests/test_websocket.py
from starlette.testclient import TestClient


def test_websocket_connection():
    with client.websocket_connect("/ws/voice/test-device") as websocket:
        websocket.send_json({"type": "auth", "token": "Bearer xxx"})
        data = websocket.receive_json()
        assert data["type"] == "auth_success"
```

---

## 11. 日志规范

```python
import logging
import sys

logger = logging.getLogger("voice-assistant")

# 配置
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(getattr(logging, settings.log_level.upper()))
```

**日志内容**:
- 会话创建/结束: `session_id`, `device_id`, `status`
- 轮次处理: `session_id`, `turn_number`, `intent`, `confidence`
- 外部 API 调用: `service`, `duration_ms`, `success/failure`
- 错误: `exception`, `stack_trace`

---

## 12. 部署清单

### 12.1 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY app/ ./app/

# 创建上传目录
RUN mkdir -p uploads/temp uploads/tts uploads/messages

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 12.2 docker-compose 更新

```yaml
# 在根目录 docker-compose.yml 中添加

voice-assistant:
  build: ./voice-assistant-service
  ports:
    - "8001:8000"
  environment:
    - DATABASE_URL=sqlite:///./voice-assistant.db
    - STT_API_KEY=${STT_API_KEY}
    - LLM_API_KEY=${LLM_API_KEY}
    - TTS_API_KEY=${TTS_API_KEY}
    - SIGNALING_SERVER_URL=http://signaling-server:8000
    - SIGNALING_API_KEY=${SIGNALING_API_KEY}
  volumes:
    - ./voice-assistant-uploads:/app/uploads
    - ./voice-assistant.db:/app/voice-assistant.db
  depends_on:
    - signaling-server
  networks:
    - elder-pi-network
```

### 12.3 启动命令

```bash
# 本地开发
cd voice-assistant-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Docker
docker-compose up --build voice-assistant
```

---

## 13. 关键实现顺序

### Phase 1: 基础骨架 (1-2 天)
1. `config.py` + `.env.example`
2. `db.py` + `models.py`
3. `main.py` + 路由注册
4. `Dockerfile` + `docker-compose.yml` 更新
5. 跑起来， health check 通

### Phase 2: 核心服务 (2-3 天)
6. `STTService` - 接入云端 STT API
7. `LLMService` - 接入大模型 API，Prompt 调优
8. `TTSService` - 接入 TTS API
9. `SignalingClient` - 对接 signaling-server

### Phase 3: 对话引擎 (2-3 天)
10. `DialogEngine.process_turn()` - 主流程
11. 状态机: 信息完整判断、确认流程、追问流程
12. 超时处理

### Phase 4: WebSocket (1-2 天)
13. `ConnectionManager`
14. `voice_websocket` 处理循环
15. 音频接收 + 处理 + 发送

### Phase 5: 消息子系统 (2-3 天)
16. `messages.py` 路由
17. 消息存储 + 通知
18. 未读消息查询 + 播放

### Phase 6: 完善 (1-2 天)
19. 异常处理 + 日志
20. 单元测试 + 集成测试
21. 性能优化 (缓存、连接池)

---

*后端设计完成，开始实现。*
