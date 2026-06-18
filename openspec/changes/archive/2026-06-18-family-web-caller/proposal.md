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
