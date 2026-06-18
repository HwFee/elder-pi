---
comet_change: elder-pi-client
role: technical-design
canonical_spec: openspec
---

# elder-pi-client Design Doc

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
