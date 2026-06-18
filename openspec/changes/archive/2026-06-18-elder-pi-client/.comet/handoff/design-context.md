# Comet Design Handoff

- Change: elder-pi-client
- Phase: design
- Mode: compact
- Context hash: 5ebb352d868fd6c731035886cc2edccdf86e8f5d2267e4247467066fae308899

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/elder-pi-client/proposal.md

- Source: openspec/changes/elder-pi-client/proposal.md
- Lines: 1-35
- SHA256: ca15666fb416c36a02b5d67ba0ec39b5b6151a6bc8c00aa111abc7a25ab7b8f5

```md
## Why

老人（被叫端）需要一个零学习成本、通电即用的树莓派客户端：自动登录/上线、醒目显示大按钮联系人、来电时全屏响铃并一键接听，通话结束自动回到待机界面。前两阶段已完成后端信令和家属网页端，本阶段补齐老人端设备软件 `elder-pi-client`。

## What Changes

- 新建 `elder-pi-client/` 目录，作为运行在 Raspberry Pi 上的全屏 Web/Electron/Python GUI 应用。
- 开机自启：系统启动后自动运行客户端并连接后端 `/signaling`。
- 设备 JWT 认证：使用预配置的 `device_token` 通过 WebSocket 认证上线。
- 大按钮联系人界面：按 `button_index` 显示联系人头像/名字，点击即可发起呼叫。
- 来电响铃：收到 `call:invite` 时全屏响铃、显示来电人信息，支持接听/拒接。
- WebRTC 视频通话：采集摄像头/麦克风，建立 P2P 连接，显示本地/远端画面。
- 通话控制：静音、关闭摄像头、挂断。
- 离线/在线状态提示：网络断开时显示重连提示。
- 部署脚本：提供 systemd 服务、Docker 或启动脚本，方便刷机后直接使用。

## Capabilities

### New Capabilities

- `pi-device-boot`: 树莓派设备启动、自动运行、持久化设备 token、首次配网/配对的引导流程。
- `pi-home-ui`: 待机主界面，大按钮显示联系人列表，支持点击发起通话。
- `pi-incoming-call`: 来电响铃、接听/拒接、超时自动拒接。
- `pi-call-session`: WebRTC 媒体连接、通话中控制、挂断与状态恢复。

### Modified Capabilities

- 无（仅消费 `video-call-signaling` 已有 Socket.IO/HTTP 能力，不改变后端 spec）。

## Impact

- 新增树莓派端技术栈（推荐 Python/Tkinter/PyQt 或全屏浏览器 + 本地服务器）。
- 新增设备 token 配置与持久化（建议写入本地文件或环境变量）。
- 需要摄像头/麦克风硬件权限及系统级自动启动配置。
- 部署方式可能新增 systemd 服务或 Docker 容器。
```

## openspec/changes/elder-pi-client/design.md

- Source: openspec/changes/elder-pi-client/design.md
- Lines: 1-61
- SHA256: 55b3da81bfb23146cb3cb9e8e579392060f90dd46c4abe3c534039c252de54d5

```md
## Context

前两阶段已完成 `video-call-signaling` 后端与 `family-web-caller` 家属网页端。老人端需要运行在 Raspberry Pi 上，面向无阅读能力、操作能力弱的老年用户，因此界面必须极简、全屏、物理按钮/大触控目标、通电即用。

## Goals / Non-Goals

**Goals:**
- 树莓派开机后自动启动并连接后端，无需老人操作。
- 待机时显示大按钮联系人，一键呼叫对应家属。
- 来电时全屏响铃并一键接听/拒接。
- 通话中全屏显示远端视频，提供静音、关闭摄像头、挂断。
- 离线时给出明确的状态提示。

**Non-Goals:**
- 不支持多人视频、文字聊天、屏幕共享。
- 不替代手机端 App（仅作为固定居所的座机式终端）。
- 不实现复杂的账号密码输入（使用预置设备 token）。

## Decisions

### 1. 技术栈：本地 WebView + Python 启动器
- **方案**：用 Python 启动一个本地静态文件服务器，加载内置 `index.html`；在 kiosk 模式 Chromium 中全屏运行（或 PyQt5 WebEngine）。
- **理由**：复用 `family-web-caller` 的 JS/Socket.IO/WebRTC 代码，老人端 UI 与家属端共享技术栈；Python 负责设备配置、系统启动、硬件按钮（可选）。
- **替代**：纯 Electron / PyQt 原生 UI。 rejected：Electron 在 Pi 上资源占用大，PyQt 做 WebRTC 复杂。

### 2. 认证：预置设备 token
- 设备创建时由家属网页端生成 token，写入树莓派 `~/.config/elder-pi/device-token`。
- 客户端启动时读取 token，通过 Socket.IO `auth: { token }` 连接后端。
- 后端通过 `device_id` claim 识别设备。

### 3. 联系人来源：后端 `/api/devices/:id/contacts`
- 启动后拉取本设备联系人，按 `button_index` 排序渲染为大按钮。
- 头像通过 `/api/uploads/:path` 加载。

### 4. 来电响铃：全屏遮罩 + 音频提示
- 收到 `call:invite` 时暂停背景音乐、显示全屏来电界面。
- 使用 HTML5 audio 播放铃声，支持接听/拒接按钮。

### 5. 部署：systemd 用户服务 + 启动脚本
- 提供 `install.sh` 创建 systemd 服务，实现开机自启。
- 提供 `run.sh` 用于本地调试。

## Risks / Trade-offs

- **树莓派性能**：WebRTC 解码 + 全屏视频可能占用较高 CPU。 mitigation：限制视频分辨率为 640x480，使用硬件加速（Chromium V4L2 codec）。
- **网络波动**：WiFi 断开后需要自动重连。 mitigation：Socket.IO 开启 reconnection，UI 显示离线提示。
- **无键盘操作**：若使用触屏，按钮尺寸不小于 120px；如配置物理按钮，通过 Python GPIO 触发页面事件。
- **Token 泄漏风险**：设备 token 写入本地文件，需限制文件权限为 600。

## Migration Plan

1. 在家属网页端创建设备并复制 device token 到树莓派。
2. 运行 `elder-pi-client/install.sh` 安装依赖并注册 systemd 服务。
3. 重启树莓派验证自动启动与上线。
4. 通过家属网页端发起呼叫验证端到端流程。

## Open Questions

1. 是否需要支持物理大按钮（GPIO）而非触屏？
2. 是否需要在 Pi 上预装 Chromium 还是使用系统默认浏览器？
3. 来电响铃音量与系统音量控制策略？
```

## openspec/changes/elder-pi-client/tasks.md

- Source: openspec/changes/elder-pi-client/tasks.md
- Lines: 1-47
- SHA256: 05bafd9eeeb5f4b6e45ce7d347b6ee82b984f82a27fb6d2ec14e94c363e53b2b

```md
## 1. Project bootstrap

- [ ] 1.1 Create `elder-pi-client/` directory with `index.html`, `src/`, `styles/`, `scripts/`
- [ ] 1.2 Add `package.json` with socket.io-client dependency and build/dev scripts
- [ ] 1.3 Add basic fullscreen CSS for Pi touchscreen (large buttons, no scrollbars)

## 2. Device boot and token loader

- [ ] 2.1 Implement `src/config.js` to read `device_token` from localStorage fallback or injected config
- [ ] 2.2 Add Python launcher `launcher.py` that reads `~/.config/elder-pi/device-token` and serves files
- [ ] 2.3 Add `install.sh` to create systemd user service for auto-start
- [ ] 2.4 Add `run.sh` for local development

## 3. Signaling client

- [ ] 3.1 Add `src/signaling.js` to connect to `/signaling` with device token
- [ ] 3.2 Handle reconnect and offline/online indicators
- [ ] 3.3 Emit and handle `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`

## 4. Home UI

- [ ] 4.1 Fetch contacts from `/api/devices/:id/contacts` on connect
- [ ] 4.2 Render contacts as large buttons ordered by `button_index`
- [ ] 4.3 Tap a contact to create an offer and emit `call_invite`
- [ ] 4.4 Show outgoing call screen while waiting

## 5. Incoming call UI

- [ ] 5.1 Show full-screen incoming call with caller name/avatar and answer/decline buttons
- [ ] 5.2 Play ringtone on `call:invite`
- [ ] 5.3 Implement answer flow: create answer, emit `call_accept`, switch to active call
- [ ] 5.4 Implement decline flow: emit `call_reject`, return home
- [ ] 5.5 Auto-decline after 60 seconds timeout

## 6. WebRTC call session

- [ ] 6.1 Add `src/webrtc.js` for `RTCPeerConnection` lifecycle (reuse patterns from family-web-caller)
- [ ] 6.2 Display local video overlay and remote video full-screen
- [ ] 6.3 Add mute, camera-off, and end-call buttons
- [ ] 6.4 Return to home on remote `call:end` or local hang-up

## 7. Deployment and verification

- [ ] 7.1 Add README with install, token setup, and run instructions
- [ ] 7.2 Build project successfully
- [ ] 7.3 Manually smoke-test boot, home, incoming call, and outgoing call against backend
- [ ] 7.4 Add minimal unit/E2E tests if feasible (e.g., signaling event routing)
```

## openspec/changes/elder-pi-client/specs/pi-call-session/spec.md

- Source: openspec/changes/elder-pi-client/specs/pi-call-session/spec.md
- Lines: 1-45
- SHA256: b6cf822f635e732f8082fb8e29e678c7315c41bf0eeadd7c2f6800543fbc9846

```md
## ADDED Requirements

### Requirement: Local and remote video are displayed during a call
The system SHALL show the local video in a small overlay and the remote video full-screen while a call is active.

#### Scenario: Active call
- **WHEN** a call is accepted or the remote party accepts
- **THEN** the remote video stream SHALL be rendered full-screen
- **AND** the local video stream SHALL be visible in a corner overlay

### Requirement: Call can be muted
The system SHALL toggle the microphone on/off when a mute button is pressed and update the button label.

#### Scenario: Mute and unmute
- **WHEN** the user presses the mute button
- **THEN** the local audio track SHALL be disabled
- **WHEN** the user presses the button again
- **THEN** the local audio track SHALL be re-enabled

### Requirement: Camera can be disabled
The system SHALL toggle the local camera on/off when a camera button is pressed.

#### Scenario: Disable and enable camera
- **WHEN** the user presses the camera-off button
- **THEN** the local video track SHALL be disabled
- **WHEN** the user presses the button again
- **THEN** the local video track SHALL be re-enabled

### Requirement: Call can be ended
The system SHALL emit `call_end`, stop media tracks, close the peer connection, and return to the home screen when the end-call button is pressed.

#### Scenario: End call
- **WHEN** the user presses the end-call button
- **THEN** the client SHALL emit `call_end`
- **AND** media tracks SHALL stop
- **AND** the peer connection SHALL close
- **AND** the UI SHALL return to the home screen

### Requirement: Remote hang-up returns to home
The system SHALL return to the home screen when a `call:end` event is received.

#### Scenario: Remote ends call
- **WHEN** a `call:end` event is received
- **THEN** the client SHALL clean up the peer connection and media
- **AND** the UI SHALL return to the home screen
```

## openspec/changes/elder-pi-client/specs/pi-device-boot/spec.md

- Source: openspec/changes/elder-pi-client/specs/pi-device-boot/spec.md
- Lines: 1-28
- SHA256: 9eb3f77b49840da0c29544fcd0ab68a2191cd5351a75dc1ea0c3e21997d23e6c

```md
## ADDED Requirements

### Requirement: Device token is loaded at startup
The system SHALL read a persisted device token from `~/.config/elder-pi/device-token` on launch.

#### Scenario: Token file exists
- **WHEN** the client starts and the token file is present
- **THEN** the client SHALL read the token and attempt to connect to the signaling server

#### Scenario: Token file missing
- **WHEN** the client starts and no token file exists
- **THEN** the client SHALL display a setup screen with instructions for pairing

### Requirement: Client starts automatically on boot
The system SHALL provide a systemd user service or init script that starts the client automatically after the graphical session is available.

#### Scenario: Reboot device
- **WHEN** the Raspberry Pi boots
- **THEN** the client SHALL start without manual login within 60 seconds

### Requirement: Client reconnects on network loss
The system SHALL automatically reconnect to the signaling server when the network becomes available again.

#### Scenario: WiFi drops and returns
- **WHEN** the network connection drops
- **THEN** the client SHALL show an offline indicator
- **WHEN** the network returns
- **THEN** the client SHALL reconnect and clear the offline indicator
```

## openspec/changes/elder-pi-client/specs/pi-home-ui/spec.md

- Source: openspec/changes/elder-pi-client/specs/pi-home-ui/spec.md
- Lines: 1-27
- SHA256: 0072dd3a6eb8a85d824cfa1c0d81fef483aaa2c12de85079e298c6ef355113f7

```md
## ADDED Requirements

### Requirement: Contacts are rendered as large buttons
The system SHALL display contacts for the device as large, tappable buttons ordered by `button_index`.

#### Scenario: Contacts loaded
- **WHEN** the client receives the contact list from `/api/devices/:id/contacts`
- **THEN** each contact SHALL be shown as a button with avatar and display name occupying at least 120px in the shorter dimension

### Requirement: Tapping a contact initiates a call
The system SHALL emit a `call_invite` event to the contact's associated user when a contact button is tapped.

#### Scenario: Outgoing call from home
- **WHEN** the user taps a contact button
- **THEN** the client SHALL create a WebRTC offer and emit `call_invite` with the contact's `user_id`
- **AND** the UI SHALL switch to the outgoing call screen

### Requirement: Home screen shows device status
The system SHALL indicate whether the device is online and ready to receive calls.

#### Scenario: Online state
- **WHEN** the socket is connected
- **THEN** a visual ready indicator SHALL be visible

#### Scenario: Offline state
- **WHEN** the socket is disconnected
- **THEN** an offline message SHALL replace or overlay the home screen
```

## openspec/changes/elder-pi-client/specs/pi-incoming-call/spec.md

- Source: openspec/changes/elder-pi-client/specs/pi-incoming-call/spec.md
- Lines: 1-31
- SHA256: 8ec811d498a7fdf018abe6f595763aebf29aa2040688924ebd8db2aed82f6808

```md
## ADDED Requirements

### Requirement: Incoming call rings and shows caller info
The system SHALL display a full-screen incoming call UI with caller name and prominent answer/decline buttons when a `call:invite` event is received.

#### Scenario: Incoming call while idle
- **WHEN** a `call:invite` event arrives
- **THEN** the client SHALL play a ringing sound and show the caller's name and avatar
- **AND** the answer button SHALL be at least 150px in the shorter dimension

### Requirement: User can answer an incoming call
The system SHALL accept the call, create an answer, and emit `call_accept` when the answer button is activated.

#### Scenario: Answer call
- **WHEN** the user presses the answer button
- **THEN** the client SHALL stop the ringtone, set the remote description, create an answer, and emit `call_accept`
- **AND** the UI SHALL switch to the active call screen

### Requirement: User can decline an incoming call
The system SHALL emit `call_reject` and return to the home screen when the decline button is activated.

#### Scenario: Decline call
- **WHEN** the user presses the decline button
- **THEN** the client SHALL emit `call_reject` and return to the home screen

### Requirement: Missed call times out
The system SHALL automatically decline an incoming call if not answered within 60 seconds.

#### Scenario: No answer
- **WHEN** 60 seconds elapse without user action
- **THEN** the client SHALL emit `call_reject` with reason `timeout` and return to the home screen
```

