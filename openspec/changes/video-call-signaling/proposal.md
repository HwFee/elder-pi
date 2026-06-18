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
