## Context

本项目首个 change 是为“老人视频通话盒”搭建后端中枢。当前没有既有代码，需要从零设计一个能同时服务家属网页端和树莓派老人端的信令与身份服务。

## Goals / Non-Goals

**Goals：**
- 提供可登录的家属账号体系与 token 认证。
- 提供联系人管理（CRUD、头像、按钮编号映射）。
- 提供 WebSocket 实时信令，让两端能完成 WebRTC 呼叫、接受、挂断。
- 提供老人端在线心跳/状态查询。
- 提供呼入白名单校验，阻止未授权呼叫。
- 保持 MVP 部署简单，能在普通 VPS/家庭服务器/树莓派本身上运行。

**Non-Goals：**
- 不实现媒体转发/SFU/MCU；媒体走 WebRTC P2P，必要时通过独立 TURN 服务器中转。
- 不支持多人会议、录音、屏幕共享。
- 不实现高可用集群、水平扩展、消息持久化（离线消息除外简单状态）。

## Decisions

### 1. 技术栈：Python 3.11+ + FastAPI + python-socketio + SQLAlchemy 2.0 + SQLite
- **理由**：Python 在树莓派生态成熟，便于后续与老人端 Python 客户端共享工具/脚本；FastAPI 提供现代异步 HTTP API 与自动文档；`python-socketio` 提供房间、重连、回退，避免原生 WebSocket 的复杂性；SQLAlchemy 2.0 是 Python 事实标准 ORM；SQLite 零运维，适合 MVP，后续可切 Postgres。
- **备选**：Node.js + Express + Socket.IO + Prisma。拒绝原因：虽然前后端同语言，但 Python 更贴近树莓派硬件/AI 扩展生态，且用户/团队倾向 Python。

### 2. 认证：JWT Access Token + Refresh Token（简单版先用单一 long-lived token）
- **理由**：无状态、易在 Socket.IO 连接时通过 auth 字段携带。MVP 先用 access token 24h 有效，后续再补 refresh token 轮换。
- **备选**：Session Cookie。拒绝原因：跨域/跨端（网页+树莓派）处理更复杂。

### 3. 实时通道：Socket.IO namespace `/signaling`
- **理由**：统一事件模型，房间内广播方便；可天然按 `roomId`（即老人端设备/用户 ID）分组。
- **事件示例**：
  - `call:invite` `{ toRoomId, callerId, callerName, offer }`
  - `call:accept` `{ callId, answer }`
  - `call:reject` `{ callId, reason }`
  - `call:end` `{ callId }`
  - `ice:candidate` `{ callId, candidate }`

### 4. 数据模型
- `User`：家属账号（id, email, passwordHash, createdAt）。
- `Device`：老人端设备（id, ownerUserId, displayName, lastSeenAt, authToken）。
- `Contact`：联系人（id, deviceId, userId, name, buttonIndex, avatarUrl）。
- `CallSession`：通话会话（id, deviceId, callerUserId, status, startedAt, endedAt）。

### 5. 白名单实现
- 呼叫请求到达时，后端检查 `Contact` 表中是否存在 `deviceId + callerUserId` 的记录；不存在则通过 Socket.IO 向 caller 发送 `call:error` 并拒绝透传 `call:invite`。

### 6. 头像存储
- MVP 存本地文件系统 `uploads/avatars/` 并通过静态路由 `/uploads/avatars/:name` 访问；后续可换对象存储。

### 7. 部署
- 单容器/单进程运行，监听 `PORT` 与 `WS_PORT`（可合一）。
- 提供 `.env.example` 与 `docker-compose.yml`。
- 树莓派老人端与家属网页端都通过环境变量配置 `SIGNALING_SERVER_URL`。

## Risks / Trade-offs

- **[风险] SQLite 并发写瓶颈**：MVP 用户量极小，可接受；后续迁移到 Postgres。
  - **缓解**：SQLAlchemy 模型使用通用列类型，迁移到 Postgres 只需改数据库 URL 与少量方言配置。
- **[风险] 单一 token 泄露**：MVP 阶段通过 HTTPS + 短有效期降低风险。
  - **缓解**：后续增加 refresh token 与设备绑定。
- **[风险] TURN 配置不在本 change 范围内**：若 P2P 打洞失败，通话可能无法建立。
  - **缓解**：设计预留 `turnConfig` 字段，由管理端下发，实际 TURN 服务器作为独立部署项。

## Open Questions

1. 是否需要一个独立的 `/ws` 原生 WebSocket 端点供非 Socket.IO 客户端使用？
2. 是否要在本阶段实现 refresh token，还是先用 24h access token？
3. 联系人头像是否需要在 elder 端本地缓存？
4. 是否允许一个家属账号管理多台老人设备？
