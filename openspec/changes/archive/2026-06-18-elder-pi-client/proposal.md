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
