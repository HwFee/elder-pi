# Brainstorm Summary

- Change: video-call-signaling
- Date: 2026-06-18

## 确认的技术方案

采用 **方案 B**：Python 3.11+ + FastAPI + `python-socketio`（ASGI）+ SQLAlchemy 2.0 + SQLite（MVP），后续可迁移到 Postgres。

- HTTP API：FastAPI 提供 `/api/auth/*`、`/api/devices/*`、`/api/contacts/*`、`/api/devices/:id/status`。
- 实时信令：`python-socketio` 命名空间 `/signaling`，按 `deviceId` 分 room；事件包括 `call:invite`、`call:accept`、`call:reject`、`call:end`、`ice:candidate`、`presence:heartbeat`。
- 数据模型：`User`、`Device`、`Contact`、`CallSession`。
- 鉴权：HTTP Bearer JWT；Socket.IO 连接时在 `auth` 字段带 token；设备使用独立 `deviceToken`。
- 头像：本地文件系统 `uploads/avatars/` + 静态路由；后续可换对象存储。
- 部署：`uvicorn` + `docker-compose`，环境变量配置。

## 关键取舍与风险

- 选择 Python 而非 Node.js：更贴合树莓派生态与后续硬件/AI 扩展；前后端不同语言带来少量上下文切换，但可接受。
- 使用 `python-socketio` 而非原生 WebSocket：保留房间、重连、广播能力，降低信令层复杂度。
- SQLite 用于 MVP：零运维，但高并发时有限；SQLAlchemy 模型保持 Postgres 兼容。
- TURN 服务器不在本 change 范围：P2P 打洞失败时可能导致无法通话，后续独立部署 coturn 等。

## 测试策略

- 单元测试：services 层使用 pytest + 内存 SQLite。
- 集成测试：HTTP API 用 `httpx`/`TestClient`；Socket.IO 事件用 `socket.io-client` Python 客户端。
- 冒烟测试：启动服务后验证注册、登录、添加联系人、邀请、接受、挂断完整链路。

## Spec Patch

无（当前 OpenSpec delta spec 已覆盖需求，无需回写）。
