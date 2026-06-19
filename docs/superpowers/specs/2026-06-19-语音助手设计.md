# 语音助手与消息子系统设计文档

**日期**: 2026-06-19  
**主题**: elder-pi 语音助手与实时语音消息子系统  
**状态**: 已确认，待实现

---

## 1. 设计目标

为 elder-pi 系统增加语音助手能力，让老人通过一个按钮完成所有操作：

- **打电话**: 按按钮 → 说话 → AI 理解 → 确认 → 自动拨号
- **发消息**: 按按钮 → 说话 → AI 理解 → 确认 → 发送语音消息
- **收消息**: 消息提示灯亮起 → 按按钮 → 自动播放所有未读语音消息

核心原则：**老人不需要看屏幕、不需要记按钮、不需要学操作，说话就行。**

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         老人端 (elder-pi-client)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ 语音助手按钮 │  │ 消息提示灯  │  │ 扬声器（播放TTS/消息）  │  │
│  │  (录音/上传) │  │  (红点/数字)│  │                         │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                                        │
│         ▼ 上传音频文件 (WebSocket / HTTP)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              voice-assistant-service (新建，Python/FastAPI)        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  STT 模块   │  │  AI 对话引擎 │  │    消息存储/通知模块     │  │
│  │ (调用云端API)│  │(调用大模型API)│  │   (SQLite/PostgreSQL)   │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘  │
│                           │                                      │
│              ┌────────────┼────────────┐                       │
│              ▼            ▼            ▼                        │
│         ┌────────┐   ┌────────┐   ┌─────────────┐               │
│         │ 打电话  │   │ 发消息  │   │ TTS 语音播报 │               │
│         │(调用signaling-server)│   │ (调用云端API)│               │
│         └────────┘   └────────┘   └─────────────┘               │
│                              │                                   │
│                              ▼ 下发音频/指令                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              signaling-server (现有，最小化扩展)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  设备/联系人  │  │  WebSocket  │  │    通话信令 (不变)       │  │
│  │   (复用)     │  │  (复用)      │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     家庭端 (family-web-caller)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  接听来电   │  │  发送语音消息 │  │  播放/查看语音消息       │  │
│  │  (现有)      │  │  (新增)      │  │  (新增)                  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 架构决策

- **voice-assistant-service 完全独立**: 有自己的数据库、自己的部署单元，不耦合 signaling-server 的内部实现
- **signaling-server 最小化扩展**: 只暴露 HTTP API 供 voice-assistant-service 调用（查询联系人、发起通话），不改现有代码
- **老人端通过 WebSocket 连接 voice-assistant-service**: 实时上传音频、接收 TTS 音频流，低延迟

---

## 3. 数据模型

### 3.1 对话会话表

管理一次"按按钮-说话-结束"的完整交互。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| device_id | TEXT | 关联 signaling-server 的 devices.id |
| status | TEXT | active / completed / timeout / error |
| created_at | DATETIME | 创建时间 |
| ended_at | DATETIME | 结束时间 |

### 3.2 对话轮次表

记录每轮对话，用于调试和 AI Prompt 优化。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| session_id | TEXT FK | 所属会话 |
| turn_number | INTEGER | 第几轮（1, 2, 3...） |
| role | TEXT | user / assistant |
| audio_url | TEXT | 语音文件路径（user 录音） |
| text | TEXT | 转写后的文字 |
| intent | TEXT | 解析意图：call / message / unknown |
| intent_data | TEXT | JSON：{target, content, ...} |
| created_at | DATETIME | 创建时间 |

### 3.3 语音消息表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| sender_device_id | TEXT | 发送方设备 ID |
| recipient_device_id | TEXT | 接收方设备 ID |
| audio_url | TEXT | 语音文件路径 |
| duration_ms | INTEGER | 语音时长（毫秒） |
| status | TEXT | unread / read |
| created_at | DATETIME | 创建时间 |
| read_at | DATETIME | 阅读时间 |

### 3.4 消息通知表

解耦消息存储和通知推送，支持 WebSocket 实时推送。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| device_id | TEXT | 接收方设备 |
| message_id | TEXT | 关联消息 |
| status | TEXT | pending / delivered / acknowledged |
| created_at | DATETIME | 创建时间 |

---

## 4. 交互流程

### 4.1 打电话流程

```
老人按语音助手按钮
    │
    ▼
老人端开始录音 ──→ 老人说话"给张三打电话"
    │
    ▼
上传音频到 voice-assistant-service
    │
    ▼
STT 转文字: "给张三打电话"
    │
    ▼
AI 理解意图: {"intent": "call", "target": "张三"}
    │
    ▼
查询联系人，确认"张三"对应 device_id
    │
    ▼
TTS 播报: "您要打电话给张三吗？请说确认或取消"
    │
    ▼
老人说"确认"
    │
    ▼
上传音频 → STT → AI 确认理解
    │
    ▼
调用 signaling-server API 发起通话
    │
    ▼
老人端进入通话界面（复用现有 webrtc.js）
```

### 4.2 发消息流程

```
老人按语音助手按钮
    │
    ▼
老人说话"告诉李四我明天去公园"
    │
    ▼
STT → AI 理解: {"intent": "message", "target": "李四", "content": "我明天去公园"}
    │
    ▼
TTS 播报: "您要给李四发消息：我明天去公园。确认吗？"
    │
    ▼
老人说"确认"
    │
    ▼
保存语音文件，创建 voice_messages 记录
    │
    ▼
创建 message_notifications 记录
    │
    ▼
通过 WebSocket 推送到接收方设备
    │
    ▼
接收方（李四的家庭端或老人端）消息提示灯亮起
```

### 4.3 收消息流程

```
老人端消息提示灯亮起（红色圆点，数字表示未读条数）
    │
    ▼
老人按语音助手按钮
    │
    ▼
AI 检查未读消息: "您有 2 条新消息，现在播放"
    │
    ▼
按顺序自动播放所有未读语音消息
    │
    ▼
播放完成后，标记所有消息为已读
    │
    ▼
消息提示灯熄灭
    │
    ▼
回到待机状态
```

### 4.4 信息不完整时的追问

```
老人说"打电话"（缺少对象）
    │
    ▼
AI 判断信息不完整
    │
    ▼
TTS 追问: "您要打给谁？"
    │
    ▼
老人说"张三"
    │
    ▼
AI 补齐信息 → 进入确认环节
```

### 4.5 超时处理

| 场景 | 行为 |
|------|------|
| 老人按按钮后 10 秒没说话 | TTS 播报"请说话"，再等待 10 秒 |
| 再次超时 | TTS 播报"操作已取消"，回到待机，结束会话 |
| AI 播报确认后 10 秒无响应 | 同上，自动取消 |
| 追问后 10 秒无响应 | 同上，自动取消 |

---

## 5. API 设计

### 5.1 voice-assistant-service 对外 API

#### WebSocket 连接

```
WS /ws/voice/{device_id}

连接建立后，双向通信：
- 客户端 → 服务端: 上传音频数据（二进制帧）
- 服务端 → 客户端: 下发 TTS 音频（二进制帧）或控制指令（JSON）
```

#### HTTP API

```
POST /api/voice/sessions
  请求: {device_id}
  响应: {session_id, status}
  说明: 创建新对话会话（老人按按钮时调用）

POST /api/voice/sessions/{session_id}/audio
  请求: multipart/form-data (audio_file)
  响应: {turn_id, text, intent, intent_data, next_action}
  说明: 上传一轮语音，返回理解和下一步动作

GET /api/messages?device_id={device_id}&status=unread
  响应: {messages: [{id, sender_name, audio_url, duration_ms, created_at}]}
  说明: 获取未读消息列表

POST /api/messages/{message_id}/read
  响应: 204
  说明: 标记消息为已读

POST /api/messages
  请求: {sender_device_id, recipient_device_id, audio_url, duration_ms}
  响应: {id}
  说明: 发送语音消息（内部 API，AI 决定发消息时调用）
```

### 5.2 signaling-server 暴露给 voice-assistant-service 的 API

```
GET /api/internal/devices/{device_id}/contacts
  响应: {contacts: [{user_id, display_name, device_id, button_index}]}
  说明: 查询设备联系人（用于 AI 匹配"张三"→device_id）

POST /api/internal/calls/invite
  请求: {call_id, caller_device_id, callee_device_id, offer}
  响应: {status}
  说明: 发起通话邀请（voice-assistant-service 构造 offer 后调用）
```

**注意**: `/api/internal/*` 需要内部服务认证（如共享 API Key），不对外暴露。

---

## 6. AI Prompt 设计

### 6.1 系统 Prompt

```
你是一个语音助手，帮助老人使用视频通话设备。你的任务是理解老人的话，
判断他是想打电话还是发消息，提取关键信息，并以 JSON 格式输出。

可用联系人列表：
{contacts_json}  // 动态注入，如 [{"name": "张三", "device_id": "xxx"}]

输出格式：
{
  "intent": "call" | "message" | "check_messages" | "unknown",
  "target": "联系人名字或null",
  "target_device_id": "匹配到的device_id或null",
  "content": "消息内容或null",
  "confidence": 0-1,
  "needs_clarification": true | false,
  "clarification_question": "如果需要追问，这里写问题"
}

规则：
1. 如果老人说"打电话"、"给XX打电话"、"叫XX过来"等，intent="call"
2. 如果老人说"告诉XX..."、"给XX发消息..."、"跟XX说..."等，intent="message"
3. 如果老人说"看看消息"、"有消息吗"，intent="check_messages"
4. 如果信息不完整（如只说"打电话"没说是谁），needs_clarification=true
5. 如果匹配不到联系人，needs_clarification=true，问"您要找谁？"
6. 如果 confidence < 0.7，needs_clarification=true
```

### 6.2 确认 Prompt

```
老人说"{user_text}"，你理解为他想{action}（{details}）。
请生成一句确认语，让老人说"确认"或"取消"。
要求：简洁、口语化、不超过 20 个字。

示例：
- "您要打电话给张三吗？请说确认或取消。"
- "您要给李四发消息：我明天去公园。确认吗？"
```

---

## 7. 老人端 UI 变更

### 7.1 新界面元素

```
┌─────────────────────────────┐
│                             │
│      [大麦克风图标]          │  ← 语音助手按钮（屏幕中央，很大）
│        按住说话              │
│                             │
│                             │
│   ● 2                       │  ← 消息提示灯（右下角，红点+数字）
│                             │
└─────────────────────────────┘
```

### 7.2 状态流转

| 状态 | 界面表现 | 说明 |
|------|----------|------|
| 待机 | 显示麦克风按钮，消息灯有未读时亮 | 默认状态 |
| 录音中 | 麦克风按钮高亮/动画，显示"正在听..." | 按住按钮或自动录音 |
| 处理中 | 显示"正在想..." | AI 处理中 |
| 播放中 | 显示"正在说..." | TTS 播放中 |
| 通话中 | 切换到现有通话界面 | 复用现有 webrtc.js |

### 7.3 删除的元素

- 联系人头像按钮网格（不再显示）
- 单独的"拨打"按钮

---

## 8. 家庭端 UI 变更

### 8.1 新增消息功能

在现有 dashboard 或 call 页面新增：

```
┌─────────────────────────────────────────┐
│  视频通话窗口                           │
│                                         │
├─────────────────────────────────────────┤
│  [消息列表]                              │
│  ┌─────────────────────────────────┐   │
│  │ 来自: 老人设备                    │   │
│  │ [▶ 播放语音] 0:32               │   │
│  │ 10:23                           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ [按住说话] 回复老人...           │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 8.2 新增 API 调用

- 获取消息列表
- 上传语音回复
- 播放语音消息

---

## 9. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| STT | 讯飞/阿里云语音转写 API | 中文准确率高，支持长语音，按量付费 |
| 大模型 | 通义千问/文心一言 API | 中文理解好，国内访问稳定 |
| TTS | 讯飞/阿里云语音合成 API | 中文自然度高，支持多种音色 |
| 后端框架 | FastAPI (Python) | 与 signaling-server 技术栈一致，WebSocket 支持好 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | 与现有项目一致 |
| 音频格式 | Opus (WebM) | 压缩率高，浏览器原生支持 |
| 音频存储 | 本地磁盘 (开发) / 对象存储 (生产) | 简单起步，可扩展 |

---

## 10. 错误处理

| 场景 | 处理 |
|------|------|
| STT 失败 | TTS 播报"我没听清，请再说一遍"，自动重录 |
| AI 理解失败 | TTS 播报"我没听懂，请再说一遍"，自动重录 |
| 联系人匹配失败 | TTS 播报"找不到这个人，您要找谁？"，追问 |
| 发起通话失败 | TTS 播报"电话打不通，稍后再试"，结束会话 |
| 发送消息失败 | TTS 播报"消息发送失败，稍后再试"，结束会话 |
| 网络断开 | 老人端显示"网络异常"，重连后恢复 |
| 服务端异常 | TTS 播报"系统繁忙，请稍后再试"，结束会话 |

---

## 11. 安全与隐私

1. **API 密钥管理**: 所有云端 API 密钥放在 voice-assistant-service 环境变量，不在老人端暴露
2. **音频文件清理**: 定期清理过期音频文件（如 30 天前），可配置保留策略
3. **传输加密**: WebSocket 使用 WSS，HTTP 使用 HTTPS
4. **内部 API 认证**: `/api/internal/*` 使用共享 API Key 或 mTLS，防止外部访问
5. **数据最小化**: 只存储必要的对话记录，支持用户删除历史

---

## 12. 部署

### 12.1 新增服务

```yaml
# docker-compose.yml 新增
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
  depends_on:
    - signaling-server
```

### 12.2 目录结构

```
video/
├── elder-pi-client/          # 现有，扩展语音助手 UI
├── signaling-server/         # 现有，最小扩展内部 API
├── family-web-caller/        # 现有，扩展消息功能
├── voice-assistant-service/  # 新建
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 入口
│   │   ├── config.py         # 配置
│   │   ├── db.py             # 数据库连接
│   │   ├── models.py         # SQLAlchemy 模型
│   │   ├── websocket.py      # WebSocket 处理
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py   # 对话会话 API
│   │   │   └── messages.py   # 消息 API
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── stt.py        # STT 服务封装
│   │   │   ├── llm.py        # 大模型服务封装
│   │   │   ├── tts.py        # TTS 服务封装
│   │   │   ├── dialog.py     # 对话管理引擎
│   │   │   └── signaling_client.py  # 调用 signaling-server
│   │   └── prompts/
│   │       ├── system.txt    # 系统 Prompt
│   │       └── confirm.txt   # 确认 Prompt
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
└── docker-compose.yml        # 更新
```

---

## 13. 实现优先级

### Phase 1: MVP（最小可用）
1. 搭建 voice-assistant-service 脚手架（目录、数据库、基本 API）
2. 实现 STT + AI 理解 + TTS 基础链路
3. 老人端：语音助手按钮 + 录音上传 + 播放 TTS
4. 实现"打电话"完整流程（单联系人，先不做消息）
5. 对接 signaling-server 内部 API

### Phase 2: 消息子系统
6. 实现语音消息存储和通知
7. 老人端：消息提示灯 + 播放未读消息
8. 家庭端：发送和接收语音消息

### Phase 3: 完善
9. 多联系人匹配优化
10. 对话历史上下文（老人可以纠正 AI）
11. 消息已读回执
12. 音频文件定期清理

---

## 14. 关键决策回顾

| 决策 | 选择 | 理由 |
|------|------|------|
| 功能范围 | 打电话 + 发消息 | 两条路一起做，完整解决老人沟通需求 |
| AI 位置 | 服务端 | 树莓派轻量，密钥安全，可扩展 |
| 消息形态 | 语音消息，实时 | 老人不用看文字，自然交互 |
| 老人端界面 | 无联系人头像，一个按钮 | 极简，老人零学习成本 |
| 交互模式 | 多轮对话，执行前确认 | 避免误操作，容错率高 |
| 多轮深度 | 智能判断 | 信息完整直接确认，不完整精准追问 |
| 技术选型 | 云端 STT + 云端大模型 + 云端 TTS | 中文效果好，按量付费，维护简单 |
| 服务架构 | 新建独立 voice-assistant-service | 职责分离，独立演进 |

---

*设计完成，待实现。*
