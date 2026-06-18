# Brainstorm Summary

- Change: family-web-caller
- Date: 2026-06-18

## 确认的技术方案

采用纯 HTML + Vanilla JS + Vite 的家属网页端：
- 登录页 (`index.html`) → 存 JWT → 跳转 dashboard
- Dashboard (`dashboard.html`)：设备列表、在线状态、联系人 CRUD、头像上传
- Call 页 (`call.html`)：WebRTC 视频通话、信令事件、媒体控制
- 模块：`api.js`（HTTP）、`auth.js`（token）、`signaling.js`（Socket.IO）、`webrtc.js`（RTCPeerConnection）、`ui.js`（DOM 辅助）
- 部署：nginx Docker 容器，统一 proxy API/WebSocket

## 关键取舍与风险

- 选择 Vanilla JS 而非框架：降低复杂度，但需保持模块清晰。
- 浏览器兼容性：主要 Chrome/Edge/Safari；WebRTC 在旧浏览器可能受限。
- P2P 打洞失败：依赖后端配置 STUN/TURN。

## 测试策略

- Vite build 验证
- 后端联调冒烟测试
- Playwright 基础 UI 测试（登录、dashboard 加载）

## Spec Patch

无
