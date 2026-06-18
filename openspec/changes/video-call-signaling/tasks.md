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
