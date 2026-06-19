# elder-pi-client 语音助手改造 — 前端对接文档

**日期**: 2026-06-19  
**状态**: 待后端完成后实现  
**负责人**: ZCode (前端部分)

---

## 背景

后端新增 `voice-assistant-service`（端口 8001），提供 AI 语音助手能力。老人端需要改造：

- **删除**: 联系人头像按钮网格（不再显示）
- **新增**: 一个大语音助手按钮 + 消息提示灯
- **核心交互**: 按按钮 → 说话 → AI 处理 → 自动打电话 / 发消息 / 播放消息

---

## 对接后端

### 1. WebSocket 连接（核心）

```
WS ws://localhost:8001/ws/voice/{device_id}

连接时发送：
{
  "type": "auth",
  "token": "Bearer {device_token}"
}

期望收到：
{
  "type": "auth_success"
}
```

**你需要实现**:
- `voice-assistant.js` — WebSocket 连接管理、音频上传、接收指令

### 2. 上传音频

```javascript
// 录音完成后，通过 WebSocket 发送
const audioBlob = /* 录音结果 */;
websocket.send(audioBlob);  // 二进制帧

// 或先通过 HTTP 上传
POST /api/voice/sessions/{session_id}/audio
Content-Type: multipart/form-data

audio: (binary)
```

### 3. 接收服务端指令

服务端会下发 JSON 指令，前端根据 `action` 执行：

```javascript
// 1. 需要确认
{
  "type": "response",
  "action": "confirm",
  "text": "您要打电话给张三吗？请说确认或取消。",
  "audio_url": "/tts/xxx.wav",  // 播放这段语音
  "data": {
    "intent": "call",
    "target": "张三",
    "target_device_id": "xxx"
  }
}

// 2. 直接执行打电话
{
  "type": "command",
  "action": "initiate_call",
  "data": {
    "call_id": "xxx",
    "target_device_id": "xxx",
    "target_name": "张三"
  }
}
// → 调用现有 webrtc.js 的 startOutgoingCall()

// 3. 播放未读消息
{
  "type": "command",
  "action": "play_messages",
  "data": {
    "messages": [
      {"id": "xxx", "audio_url": "/uploads/xxx.wav", "sender_name": "李四"}
    ]
  }
}
// → 按顺序播放语音

// 4. 消息发送成功
{
  "type": "command",
  "action": "message_sent",
  "data": {
    "recipient": "李四"
  }
}

// 5. 错误
{
  "type": "response",
  "action": "error",
  "text": "我没听清，请再说一遍",
  "audio_url": "/tts/retry.wav"
}
```

---

## UI 改造

### 1. 删除

- `contacts-grid` 及其所有子元素（联系人头像按钮）
- 相关的 `renderContacts()`、`handleContactClick()` 逻辑

### 2. 新增界面

```html
<!-- index.html 改造后 -->
<div id="home-screen">
  <!-- 大语音助手按钮 -->
  <button id="voice-btn">
    <svg><!-- 麦克风图标 --></svg>
    <span>按住说话</span>
  </button>
  
  <!-- 消息提示灯 -->
  <div id="msg-badge" hidden>
    <span id="msg-count">0</span>
  </div>
  
  <!-- 状态文字 -->
  <div id="status-text">按按钮开始</div>
</div>

<!-- 新增：录音中状态 -->
<div id="recording-screen" hidden>
  <div class="recording-animation"></div>
  <div id="recording-text">正在听...</div>
</div>

<!-- 新增：AI 处理中状态 -->
<div id="processing-screen" hidden>
  <div class="spinner"></div>
  <div id="processing-text">正在想...</div>
</div>

<!-- 新增：播放消息状态 -->
<div id="playing-screen" hidden>
  <div class="playing-animation"></div>
  <div id="playing-text">播放消息中...</div>
</div>
```

### 3. 状态流转

```
待机 (home-screen)
  │ 按 voice-btn
  ▼
录音中 (recording-screen) ──→ 松开按钮 ──→ 上传音频
  │                              ▼
  │                        处理中 (processing-screen)
  │                              │
  │              ┌───────────────┼───────────────┐
  │              ▼               ▼               ▼
  │           [需确认]        [直接执行]      [播放消息]
  │              │               │               │
  │              ▼               ▼               ▼
  │         回到待机      进入通话界面    播放消息
  │                            │               │
  │                            ▼               ▼
  │                         通话结束        回到待机
  │                            │
  │                            ▼
  │                         回到待机
  │
  └─ 超时 ──→ 回到待机
```

---

## 需要新建的文件

| 文件 | 说明 |
|------|------|
| `src/voice-assistant.js` | WebSocket 连接、录音、音频播放、状态管理 |
| `src/recorder.js` | 浏览器录音封装（MediaRecorder API） |

## 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `index.html` | 删除 contacts-grid，新增 voice-btn、msg-badge、新 screen |
| `src/main.js` | 删除联系人加载/渲染逻辑，接入 voice-assistant.js |
| `styles/main.css` | 新增语音按钮、消息提示灯、录音动画样式 |

---

## 录音实现（recorder.js）

```javascript
// 你需要实现：

class VoiceRecorder {
  async start() {
    // 1. 获取麦克风权限
    // 2. 创建 MediaRecorder，格式：audio/webm;codecs=opus
    // 3. 开始录音
    // 4. 收集音频数据到 Blob
  }
  
  stop() {
    // 1. 停止 MediaRecorder
    // 2. 返回 Blob
  }
  
  async play(audioUrl) {
    // 播放服务端下发的音频（TTS 或消息）
  }
}
```

**注意**:
- 录音格式用 `audio/webm;codecs=opus`，兼容性好、压缩率高
- 录音时长限制：最长 60 秒（服务端也有限制）
- 需要处理用户拒绝麦克风权限的情况

---

## 消息提示灯

```javascript
// 你需要实现：

// 1. 检查未读消息（启动时 + 定时轮询）
async function checkUnreadMessages() {
  const res = await fetch(`${VOICE_API_URL}/api/messages?device_id=${deviceId}&status=unread`);
  const data = await res.json();
  updateMessageBadge(data.total);
}

// 2. 更新提示灯
function updateMessageBadge(count) {
  const badge = document.getElementById('msg-badge');
  const countEl = document.getElementById('msg-count');
  if (count > 0) {
    badge.hidden = false;
    countEl.textContent = count;
  } else {
    badge.hidden = true;
  }
}

// 3. 播放消息后标记已读
async function markMessageRead(messageId) {
  await fetch(`${VOICE_API_URL}/api/messages/${messageId}/read`, {method: 'POST'});
}
```

---

## 配置变更

`src/config.js` 新增：

```javascript
export function getVoiceAssistantUrl() {
  // 开发环境
  return 'http://localhost:8001';
  // 生产环境从环境变量或配置文件读取
}

export function getVoiceWsUrl() {
  return 'ws://localhost:8001';
}
```

---

## 实现顺序（建议）

### Step 1: UI 骨架
1. 修改 `index.html` — 删除 contacts-grid，新增 voice-btn、msg-badge
2. 修改 `styles/main.css` — 语音按钮样式（大、居中、醒目）
3. 修改 `src/main.js` — 删除联系人相关逻辑，保留通话逻辑

### Step 2: 录音功能
4. 新建 `src/recorder.js` — 封装 MediaRecorder
5. 测试：按住按钮录音，松开后拿到 Blob，能播放

### Step 3: WebSocket 连接
6. 新建 `src/voice-assistant.js` — 连接 WS、发送音频、接收指令
7. 测试：按住录音 → 上传 → 收到服务端响应（先用 mock）

### Step 4: 对接后端
8. 后端完成后，联调完整流程：
   - 录音 → STT → AI 理解 → 确认 → 打电话
   - 录音 → STT → AI 理解 → 确认 → 发消息

### Step 5: 消息功能
9. 实现消息提示灯（轮询未读消息）
10. 实现播放消息功能

### Step 6: 完善
11. 错误处理（没听清、网络断开、超时）
12. 动画和反馈（录音中动画、处理中 spinner）
13. 测试各种边界情况

---

## 关键接口汇总

| 接口 | 方法 | 路径 | 用途 |
|------|------|------|------|
| WebSocket | WS | `/ws/voice/{device_id}` | 实时语音交互 |
| 创建会话 | POST | `/api/voice/sessions` | 按按钮时创建 |
| 上传音频 | POST | `/api/voice/sessions/{id}/audio` | 上传录音 |
| 获取消息 | GET | `/api/messages?device_id=xxx&status=unread` | 查未读消息 |
| 标记已读 | POST | `/api/messages/{id}/read` | 消息播放后 |

---

## 注意事项

1. **WebSocket 断线重连**：网络波动时要自动重连，恢复会话
2. **音频格式**：录音用 webm/opus，播放支持 wav/mp3（看 TTS 返回什么）
3. **并发控制**：同一时间只能有一个录音/处理流程，防止重复按按钮
4. **错误提示**：所有错误都用语音播报（TTS），老人不看文字
5. **性能**：录音文件可能较大，考虑分片上传或压缩

---

*后端完成后，按此文档实现前端。有问题随时沟通。*
