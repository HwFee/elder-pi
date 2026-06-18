# Comet Design Handoff

- Change: video-call-signaling
- Phase: design
- Mode: compact
- Context hash: f3ce0f556f9ac443caa4ac49183a1757e4bd2a16b7b77b135e6d972c8b299d69

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/video-call-signaling/proposal.md

- Source: openspec/changes/video-call-signaling/proposal.md
- Lines: 1-33
- SHA256: 0c340e7aba73c7e6e8d74f2a7078483ff8559de89c61b6ac6a98e4cd51735837

```md
## Why

为了把树莓派变成不识字老人也能用的视频通话终端，需要先有一个稳定、安全、可扩展的互联网信令与身份服务。它负责把“家属网页端”和“老人树莓派端”连接起来，管理联系人、权限和通话邀请，否则两端无法在互联网上互相发现、接通或挂断。

## What Changes

- 新建一个信令与身份后端服务，提供 HTTP REST API 与 WebSocket 实时通道。
- 新增用户/家属账号登录与 token 认证能力。
- 新增联系人管理：家属可为老人端添加/编辑/删除联系人，包含头像、昵称、按钮编号映射。
- 新增白名单机制：只有联系人列表中的家属才能向对应老人端发起通话。
- 新增通话控制信令：邀请、接受、拒绝、挂断、ICE 候选转发。
- 新增老人端在线状态/心跳接口，供家属端查看是否在线。

## Capabilities

### New Capabilities

- `user-auth`: 家属账号注册、登录、JWT/token 认证与登出。
- `contact-management`: 联系人 CRUD，头像存储，老人端实体按钮编号与联系人映射。
- `call-signaling`: WebSocket 通话邀请、接受、拒绝、挂断及 ICE 候选中转。
- `presence`: 老人端心跳与在线状态查询。
- `whitelist`: 基于联系人列表的呼入白名单校验。

### Modified Capabilities

- 无（项目尚无已有 capability）。

## Impact

- 引入新的后端运行时与依赖（如 Node.js/Express 或 Python/FastAPI）。
- 引入持久化数据库（SQLite/Postgres）用于用户、联系人、在线状态。
- 引入 WebSocket 长连接服务，影响部署与负载考量。
- 后续 `family-web-caller` 与 `elder-pi-client` 两个 change 都依赖本服务提供的 API/WebSocket 契约。
```

## openspec/changes/video-call-signaling/design.md

- Source: openspec/changes/video-call-signaling/design.md
- Lines: 1-70
- SHA256: a3c5cea712d826e71be8308073dc4c1c0cd8ff9e0dc5ace4a564daee15a49be8

```md
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
```

## openspec/changes/video-call-signaling/tasks.md

- Source: openspec/changes/video-call-signaling/tasks.md
- Lines: 1-51
- SHA256: 76042fa850698d6b9919d6f08cbae85da4914ccd6174838c17048b40e5fcd870

```md
## 1. Project bootstrap

- [ ] 1.1 Initialize Node.js project with TypeScript, Express, Socket.IO, Prisma, SQLite
- [ ] 1.2 Add dev tooling: ESLint, Prettier, tsx/nodemon, basic test runner
- [ ] 1.3 Create `.env.example` and `docker-compose.yml`
- [ ] 1.4 Define Prisma schema for User, Device, Contact, CallSession

## 2. User authentication

- [ ] 2.1 Implement `POST /api/auth/register` with password hashing
- [ ] 2.2 Implement `POST /api/auth/login` with JWT issuance
- [ ] 2.3 Add JWT middleware for protected HTTP routes
- [ ] 2.4 Add tests for register/login/invalid credentials

## 3. Device & contact management

- [ ] 3.1 Implement `POST /api/devices` to register an elder device
- [ ] 3.2 Implement `POST /api/devices/:deviceId/contacts`
- [ ] 3.3 Implement `GET /api/devices/:deviceId/contacts`
- [ ] 3.4 Implement `PATCH /api/contacts/:contactId` and `DELETE /api/contacts/:contactId`
- [ ] 3.5 Enforce button-index uniqueness per device
- [ ] 3.6 Add avatar upload endpoint and static file serving
- [ ] 3.7 Add ownership/authorization checks on all device/contact routes

## 4. Presence

- [ ] 4.1 Implement `presence:heartbeat` Socket.IO event to update `lastSeenAt`
- [ ] 4.2 Implement `GET /api/devices/:deviceId/status` online check
- [ ] 4.3 Add periodic cleanup/timeout logic for stale connections

## 5. Call signaling

- [ ] 5.1 Implement Socket.IO `connection` auth using JWT and device token
- [ ] 5.2 Implement `call:invite` validation and forwarding
- [ ] 5.3 Implement `call:accept`, `call:reject`, `call:end` forwarding
- [ ] 5.4 Implement `ice:candidate` relay
- [ ] 5.5 Implement single-active-call guard (`call:busy`)
- [ ] 5.6 Record CallSession lifecycle in database

## 6. Whitelist

- [ ] 6.1 Verify caller is in target device's contacts before forwarding `call:invite`
- [ ] 6.2 Return `call:error` for unauthorized callers
- [ ] 6.3 Add tests for authorized/unauthorized scenarios

## 7. Deployment & docs

- [ ] 7.1 Write README with run/dev/test instructions
- [ ] 7.2 Add seed script for local demo
- [ ] 7.3 Verify service starts and passes basic smoke tests
- [ ] 7.4 Document WebSocket event schema for frontend and Pi clients
```

## openspec/changes/video-call-signaling/specs/call-signaling/spec.md

- Source: openspec/changes/video-call-signaling/specs/call-signaling/spec.md
- Lines: 1-43
- SHA256: 1ecc01bb04979b2d44634d4b3e64f5552ddbb8e3222f39a80ec46ecc919776fd

```md
## ADDED Requirements

### Requirement: Invite a device to a call
The system SHALL forward a call invitation from an authenticated caller to the target elder device over WebSocket.

#### Scenario: Caller invites elder device
- **WHEN** an authenticated caller emits `call:invite` with a valid target device id and WebRTC offer
- **THEN** the system validates the caller is whitelisted and forwards the invitation to the elder device

### Requirement: Accept a call
The system SHALL forward an accept event from the elder device back to the caller.

#### Scenario: Elder device accepts
- **WHEN** the elder device emits `call:accept` with the call id and WebRTC answer
- **THEN** the system forwards the event to the original caller

### Requirement: Reject a call
The system SHALL forward a reject event from the elder device to the caller.

#### Scenario: Elder device rejects
- **WHEN** the elder device emits `call:reject` with the call id
- **THEN** the system forwards the event to the caller and closes the call session

### Requirement: End a call
The system SHALL forward an end event from either side to the other side and record the call as ended.

#### Scenario: Caller ends call
- **WHEN** the caller emits `call:end` with the call id
- **THEN** the system forwards the event to the elder device and updates the call session status to ended

### Requirement: Relay ICE candidates
The system SHALL relay ICE candidates between caller and elder device during a call.

#### Scenario: Caller sends ICE candidate
- **WHEN** the caller emits `ice:candidate` with the call id and candidate payload
- **THEN** the system forwards the candidate to the elder device

### Requirement: Single active call per device
The system SHALL reject a new invitation if the elder device already has an active call.

#### Scenario: Device busy
- **WHEN** a caller invites a device that already has an active call
- **THEN** the system returns `call:busy` to the caller
```

## openspec/changes/video-call-signaling/specs/contact-management/spec.md

- Source: openspec/changes/video-call-signaling/specs/contact-management/spec.md
- Lines: 1-40
- SHA256: c18d8e5106435c6f858f293bcae765736b517dd7ad11f0f581812c4a5bbab455

```md
## ADDED Requirements

### Requirement: Create contact
The system SHALL allow an authenticated family member to create a contact for an elder device with a name, optional avatar, and optional button index.

#### Scenario: Successful contact creation
- **WHEN** an authenticated user posts valid contact data to `POST /api/devices/{deviceId}/contacts`
- **THEN** the system stores the contact and returns its id

### Requirement: List contacts
The system SHALL return all contacts for a given elder device.

#### Scenario: Device owner lists contacts
- **WHEN** the device owner requests `GET /api/devices/{deviceId}/contacts`
- **THEN** the system returns the contact list

#### Scenario: Unauthorized user lists contacts
- **WHEN** a user who does not own the device requests the contact list
- **THEN** the system returns a 403 error

### Requirement: Update contact
The system SHALL allow an authenticated owner to update a contact's name, avatar, or button index.

#### Scenario: Successful update
- **WHEN** the device owner sends a valid `PATCH /api/contacts/{contactId}`
- **THEN** the system updates the contact and returns the updated record

### Requirement: Delete contact
The system SHALL allow an authenticated owner to delete a contact.

#### Scenario: Successful deletion
- **WHEN** the device owner sends `DELETE /api/contacts/{contactId}`
- **THEN** the system removes the contact and returns 204

### Requirement: Button index uniqueness
The system SHALL ensure a button index is unique per elder device when assigned.

#### Scenario: Duplicate button index
- **WHEN** the owner creates a contact with a button index already used on the same device
- **THEN** the system returns a 409 error
```

## openspec/changes/video-call-signaling/specs/presence/spec.md

- Source: openspec/changes/video-call-signaling/specs/presence/spec.md
- Lines: 1-19
- SHA256: a41b1a6dbd30e30a86c200df6b8b2e162700533fe7d89d0dc6325f8d3ab93b83

```md
## ADDED Requirements

### Requirement: Heartbeat
The system SHALL receive periodic heartbeats from an elder device to track liveness.

#### Scenario: Elder device sends heartbeat
- **WHEN** the elder device emits `presence:heartbeat` over its authenticated WebSocket connection
- **THEN** the system updates the device's `lastSeenAt` timestamp

### Requirement: Query device online status
The system SHALL allow an authenticated family member to query whether an elder device is currently online.

#### Scenario: Online device
- **WHEN** an authenticated user requests `GET /api/devices/{deviceId}/status`
- **THEN** the system returns `online: true` if the device has sent a heartbeat within the configured timeout window

#### Scenario: Offline device
- **WHEN** an authenticated user requests status for a device that has not sent a heartbeat within the timeout window
- **THEN** the system returns `online: false`
```

## openspec/changes/video-call-signaling/specs/user-auth/spec.md

- Source: openspec/changes/video-call-signaling/specs/user-auth/spec.md
- Lines: 1-34
- SHA256: 5612055ada2a2edbe86a02c88eb13343697e37f6774c789d132bb14a0d08caf9

```md
## ADDED Requirements

### Requirement: User registration
The system SHALL allow a new family member to register with a unique email and a password.

#### Scenario: Successful registration
- **WHEN** a user submits a valid email and password to `POST /api/auth/register`
- **THEN** the system creates an account and returns the user id

#### Scenario: Duplicate email
- **WHEN** a user registers with an email that already exists
- **THEN** the system returns a 409 error

### Requirement: User login
The system SHALL authenticate a registered user and return an access token.

#### Scenario: Successful login
- **WHEN** a user submits correct email and password to `POST /api/auth/login`
- **THEN** the system returns a JWT access token

#### Scenario: Invalid credentials
- **WHEN** a user submits an incorrect password
- **THEN** the system returns a 401 error

### Requirement: Token validation
The system SHALL reject requests with missing or invalid tokens for protected endpoints.

#### Scenario: Valid token
- **WHEN** a request includes a valid access token in the `Authorization` header
- **THEN** the system allows access and identifies the caller

#### Scenario: Missing token
- **WHEN** a request omits the access token
- **THEN** the system returns a 401 error
```

## openspec/changes/video-call-signaling/specs/whitelist/spec.md

- Source: openspec/changes/video-call-signaling/specs/whitelist/spec.md
- Lines: 1-19
- SHA256: 80099b6345bae78120fe96a26b9af1d722caab79fa3037fc3f86672069e68364

```md
## ADDED Requirements

### Requirement: Whitelist-based call permission
The system SHALL only forward a call invitation if the caller is a contact of the target elder device.

#### Scenario: Authorized caller
- **WHEN** an authenticated caller who is in the target device's contact list emits `call:invite`
- **THEN** the system forwards the invitation to the elder device

#### Scenario: Unauthorized caller
- **WHEN** an authenticated caller who is not in the target device's contact list emits `call:invite`
- **THEN** the system emits `call:error` to the caller with a forbidden reason and does not forward the invitation

### Requirement: Contact deletion revokes permission
The system SHALL treat a deleted contact as no longer authorized to call the device.

#### Scenario: Former caller is removed
- **WHEN** a previously authorized contact is deleted from the device
- **THEN** any subsequent `call:invite` from that user is rejected
```

