# Comet Design Handoff

- Change: family-web-caller
- Phase: design
- Mode: compact
- Context hash: 8522d5c5eae9e674cb879c05318492d89a100b7928f81253f6dff27df9e6c595

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/family-web-caller/proposal.md

- Source: openspec/changes/family-web-caller/proposal.md
- Lines: 1-31
- SHA256: cf28685ce07102ab5b1ee7cfbbe79d697a02a3b720f30ba530bc4a9fc52e7b5c

```md
## Why

老人端树莓派需要家属主动发起视频通话，也需要一个家属能登录、查看设备在线状态、发起呼叫并管理联系人的入口。当前项目只有后端信令服务，缺少面向家属的网页端，因此需要新建 `family-web-caller`。

## What Changes

- 新建一个静态/SSR 家属网页应用，部署为 `family-web-caller/`。
- 提供登录页：使用后端 `POST /api/auth/login` 获取 JWT。
- 提供联系人管理后台：增删改查老人端联系人、上传头像、映射按钮编号。
- 提供呼叫界面：查看老人设备在线状态，一键发起 WebRTC 视频通话。
- 提供接听界面：作为被叫时响铃并显示老人端画面。
- 通过 Socket.IO `/signaling` 与后端进行信令交互。
- 使用 WebRTC `getUserMedia` / `RTCPeerConnection` 进行媒体采集与 P2P 连接。

## Capabilities

### New Capabilities

- `family-auth`: 家属网页端登录与 token 存储。
- `family-dashboard`: 设备列表、在线状态、联系人 CRUD 与头像上传。
- `family-call-ui`: 发起/接听视频通话的 WebRTC 界面与信令交互。

### Modified Capabilities

- 无（仅消费后端已有 API/WebSocket，不改变后端 spec）。

## Impact

- 新增前端技术栈（推荐纯 HTML/JS 或 Vue/React 单页应用）。
- 新增对后端 `video-call-signaling` 服务的 HTTP 与 WebSocket 依赖。
- 可能影响 CORS 配置与部署方式（建议通过 nginx 或 docker-compose 统一暴露）。
```

## openspec/changes/family-web-caller/design.md

- Source: openspec/changes/family-web-caller/design.md
- Lines: 1-74
- SHA256: 368d195cf51852b899661cac9120a98061b2d89d937d7445a8765e98144b7ccb

```md
## Context

后端 `video-call-signaling` 已提供认证、设备/联系人管理、在线状态、WebRTC 信令。本 change 为家属提供一个浏览器端应用，用于登录、管理联系人、查看在线状态、发起和接听视频通话。

## Goals / Non-Goals

**Goals：**
- 提供登录页，使用后端 JWT 认证。
- 提供设备管理后台：查看老人设备、在线状态、管理联系人（头像/按钮编号）。
- 提供视频通话界面：发起呼叫、接听呼叫、挂断、显示本地/远端视频。
- 通过 Socket.IO 与后端信令服务通信。
- 使用 WebRTC 与老人端建立 P2P 视频通话。
- 保持前端简单、可静态部署或单容器运行。

**Non-Goals：**
- 不实现群聊、多人会议、屏幕共享。
- 不实现复杂的状态管理库或移动端原生 App。
- 不实现 TURN 服务器（仅使用后端可配置的 TURN）。
- 不实现实时消息/聊天。

## Decisions

### 1. 技术栈：纯 HTML + Vanilla JS + Vite
- **理由**：项目面向家庭场景，前端不需要复杂框架；Vite 提供现代开发体验、热更新、打包；纯 JS 便于不依赖 React/Vue 生态，降低维护成本。
- **备选**：Vue/React。拒绝原因：过度设计，当前需求用原生 JS 即可满足。

### 2. 通信：axios/fetch + socket.io-client
- **理由**：后端已使用 Socket.IO；HTTP 用 fetch 即可，无需额外依赖。
- **备选**：原生 WebSocket。拒绝原因：需自行实现 Socket.IO 协议，没必要。

### 3. 页面结构
```
family-web-caller/
├── index.html          # 登录页
├── dashboard.html      # 设备与联系人管理
├── call.html           # 视频通话界面
├── src/
│   ├── api.js          # HTTP API 封装
│   ├── auth.js         # 登录/token
│   ├── signaling.js    # Socket.IO 连接与事件
│   ├── webrtc.js       # RTCPeerConnection 封装
│   ├── ui.js           # DOM 渲染辅助
│   └── main.js         # 页面初始化
├── public/
│   └── style.css
├── Dockerfile
├── nginx.conf
└── package.json
```

### 4. 状态管理
- 使用简单的模块级变量和自定义事件（`EventTarget`）。不使用 Redux/Pinia。

### 5. WebRTC 策略
- 使用 P2P，ICE 服务器从后端获取或环境变量注入。
- 视频优先，音频可选。
- 呼叫建立流程：创建 offer → 发送 `call:invite` → 等待 `call:accept` + answer → 设置 remote description → 交换 ICE。

### 6. 部署
- 使用 nginx 容器提供静态文件。
- 通过 `docker-compose.yml` 与后端服务一起编排。
- 后端地址通过环境变量 `VITE_API_URL` / `VITE_WS_URL` 注入。

## Risks / Trade-offs

- **[风险] 浏览器兼容性**：iOS Safari 对 WebRTC 支持较弱。缓解：测试 Safari/Chrome，必要时简化约束。
- **[风险] 无框架导致代码增长后难维护**。缓解：保持模块单一职责，文件不超过 300 行。
- **[风险] P2P 打洞失败**。缓解：通过后端配置 STUN/TURN，TURN 作为独立服务。

## Open Questions

1. 是否需要响铃/震动提示？
2. 是否需要通话计时显示？
3. 是否支持多个老人设备切换？
```

## openspec/changes/family-web-caller/tasks.md

- Source: openspec/changes/family-web-caller/tasks.md
- Lines: 1-50
- SHA256: 8f67ede4b779a6309da21894ddb042bee3c072047d499f1651b6a0049b17ae4a

```md
## 1. Project bootstrap

- [ ] 1.1 Initialize Vite project under `family-web-caller/`
- [ ] 1.2 Add `index.html`, `dashboard.html`, `call.html`
- [ ] 1.3 Add basic CSS and shared layout

## 2. Authentication

- [ ] 2.1 Implement login page (`index.html`)
- [ ] 2.2 Add `api.js` wrapper for backend HTTP calls
- [ ] 2.3 Add `auth.js` for JWT storage/retrieval/logout
- [ ] 2.4 Protect dashboard and call pages by redirecting unauthenticated users

## 3. Dashboard

- [ ] 3.1 Fetch and render device list
- [ ] 3.2 Fetch and render contacts for selected device
- [ ] 3.3 Add contact form (create/update)
- [ ] 3.4 Add contact delete with confirmation
- [ ] 3.5 Add avatar upload preview and submit

## 4. Signaling client

- [ ] 4.1 Add `signaling.js` using `socket.io-client`
- [ ] 4.2 Connect with user JWT and handle reconnect
- [ ] 4.3 Emit and handle `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`
- [ ] 4.4 Handle `call:busy` and `call:error`

## 5. WebRTC call UI

- [ ] 5.1 Add `webrtc.js` wrapping `RTCPeerConnection`
- [ ] 5.2 Create offer on outgoing call
- [ ] 5.3 Create answer on incoming call
- [ ] 5.4 Display local and remote video
- [ ] 5.5 Add mute and camera-off toggles
- [ ] 5.6 Add end-call button

## 6. Deployment

- [ ] 6.1 Add `Dockerfile` with nginx static server
- [ ] 6.2 Add `nginx.conf` to proxy API/WebSocket to backend
- [ ] 6.3 Update root `docker-compose.yml` to include family-web-caller
- [ ] 6.4 Add README with dev/build/run instructions

## 7. Verification

- [ ] 7.1 Build project successfully
- [ ] 7.2 Manually smoke-test login, dashboard, call flow against backend
- [ ] 7.3 Add Playwright or basic UI tests for critical paths
- [ ] 7.4 Run full verification
```

## openspec/changes/family-web-caller/specs/family-auth/spec.md

- Source: openspec/changes/family-web-caller/specs/family-auth/spec.md
- Lines: 1-23
- SHA256: 2b92f222d041974c8d06572ed544cd54fa10562488d02d0ddc494a31ba4fe800

```md
## ADDED Requirements

### Requirement: Login form
The system SHALL provide a login form that collects email and password.

#### Scenario: Successful login
- **WHEN** a family member enters valid credentials and submits
- **THEN** the system stores the JWT and redirects to the dashboard

#### Scenario: Invalid credentials
- **WHEN** a family member enters invalid credentials
- **THEN** the system displays an error message and stays on the login page

### Requirement: Token storage
The system SHALL store the JWT securely for subsequent authenticated requests.

#### Scenario: Token persists across reloads
- **WHEN** a logged-in user reloads the page
- **THEN** the token is still available and requests remain authenticated

#### Scenario: Token cleared on logout
- **WHEN** a user clicks logout
- **THEN** the token is removed and the user is redirected to login
```

## openspec/changes/family-web-caller/specs/family-call-ui/spec.md

- Source: openspec/changes/family-web-caller/specs/family-call-ui/spec.md
- Lines: 1-64
- SHA256: 5610680cb6a823dadf61aa273dabfd37c4e21de2f1b522f9c07add918a47a64f

```md
## ADDED Requirements

### Requirement: Initiate call
The system SHALL allow a family member to initiate a video call to an elder device.

#### Scenario: Start call
- **WHEN** a user clicks the call button on a contact
- **THEN** the system creates a WebRTC offer, sends `call:invite`, and shows the call UI

#### Scenario: Callee accepts
- **WHEN** the elder device emits `call:accept`
- **THEN** the system sets the remote description and displays the remote video

#### Scenario: Callee rejects
- **WHEN** the elder device emits `call:reject`
- **THEN** the system shows a rejected message and closes the call UI

#### Scenario: Callee busy
- **WHEN** the server emits `call:busy`
- **THEN** the system shows a busy message and closes the call UI

### Requirement: Receive call
The system SHALL display an incoming call screen when the server forwards a `call:invite`.

#### Scenario: Incoming call
- **WHEN** the server emits `call:invite` for the logged-in user
- **THEN** the system plays a ringtone, shows the caller name, and provides accept/reject buttons

#### Scenario: Accept incoming call
- **WHEN** a user clicks accept
- **THEN** the system creates an answer, emits `call:accept`, and opens the call UI

### Requirement: End call
The system SHALL allow either side to end the active call.

#### Scenario: User ends call
- **WHEN** a user clicks the hang-up button
- **THEN** the system emits `call:end` and closes the call UI

#### Scenario: Remote ends call
- **WHEN** the server emits `call:end`
- **THEN** the system closes the call UI

### Requirement: ICE relay
The system SHALL send and receive ICE candidates during a call.

#### Scenario: Send ICE candidate
- **WHEN** the local peer connection gathers a candidate
- **THEN** the system emits `ice:candidate` to the server

#### Scenario: Receive ICE candidate
- **WHEN** the server emits `ice:candidate`
- **THEN** the system adds the candidate to the peer connection

### Requirement: Media controls
The system SHALL provide mute and camera-off toggles during a call.

#### Scenario: Mute audio
- **WHEN** a user clicks the mute button
- **THEN** the local audio track is disabled

#### Scenario: Disable camera
- **WHEN** a user clicks the camera-off button
- **THEN** the local video track is disabled and the remote side sees a placeholder
```

## openspec/changes/family-web-caller/specs/family-dashboard/spec.md

- Source: openspec/changes/family-web-caller/specs/family-dashboard/spec.md
- Lines: 1-43
- SHA256: 84aa426a608cfb109a9afc75341bacbe1546d57e2b15d6808e8e61ad37cd6a33

```md
## ADDED Requirements

### Requirement: Device list
The system SHALL display a list of elder devices owned by the logged-in user.

#### Scenario: Device online
- **WHEN** the dashboard loads
- **THEN** each device shows its display name and online status

### Requirement: Contact list
The system SHALL display contacts for a selected device.

#### Scenario: View contacts
- **WHEN** a user selects a device
- **THEN** the system shows contacts with avatar, name, and button index

### Requirement: Create contact
The system SHALL allow the user to add a new contact for a device.

#### Scenario: Add contact
- **WHEN** a user fills in name, selects button index, and saves
- **THEN** the contact appears in the list

### Requirement: Update contact
The system SHALL allow the user to edit a contact's name, button index, or avatar.

#### Scenario: Edit contact
- **WHEN** a user changes contact information and saves
- **THEN** the contact is updated in the list

### Requirement: Delete contact
The system SHALL allow the user to remove a contact.

#### Scenario: Remove contact
- **WHEN** a user confirms deletion of a contact
- **THEN** the contact disappears from the list and the caller loses permission

### Requirement: Avatar upload
The system SHALL allow uploading an avatar image for a contact.

#### Scenario: Upload avatar
- **WHEN** a user selects an image file and saves
- **THEN** the avatar is displayed for that contact
```

