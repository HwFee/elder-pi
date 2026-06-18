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
