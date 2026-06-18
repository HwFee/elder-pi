## 1. Project bootstrap

- [x] 1.1 Initialize Python project with FastAPI, python-socketio, SQLAlchemy, aiosqlite
- [x] 1.2 Add dev tooling: pytest, pytest-asyncio, httpx
- [x] 1.3 Create `requirements.txt`, `.env.example`, `pytest.ini`
- [x] 1.4 Add `app/config.py` with Pydantic Settings

## 2. Database layer

- [x] 2.1 Create SQLAlchemy async engine/session and `Base`
- [x] 2.2 Define ORM models: `User`, `Device`, `Contact`, `CallSession`
- [x] 2.3 Add unique constraint on `(device_id, button_index)`

## 3. Schemas and dependencies

- [x] 3.1 Create Pydantic request/response schemas
- [x] 3.2 Add `get_current_user` JWT dependency for protected routes

## 4. User authentication

- [x] 4.1 Implement password hashing with bcrypt
- [x] 4.2 Implement JWT create/decode helpers (HS256)
- [x] 4.3 Implement `POST /api/auth/register` and `POST /api/auth/login`
- [x] 4.4 Add auth tests

## 5. Device management

- [x] 5.1 Implement device registration and JWT device token
- [x] 5.2 Implement `GET /api/devices` and `GET /api/devices/{device_id}`
- [x] 5.3 Enforce device ownership checks

## 6. Contact management

- [x] 6.1 Implement contact CRUD routes
- [x] 6.2 Enforce button-index uniqueness per device
- [x] 6.3 Add ownership checks via `Device` join

## 7. Avatar upload

- [x] 7.1 Implement avatar save with type/size validation
- [x] 7.2 Add `POST /api/contacts/{contact_id}/avatar`
- [x] 7.3 Mount `/uploads` static files

## 8. Presence

- [x] 8.1 Implement `ConnectionManager` for online state and heartbeat
- [x] 8.2 Implement `presence:heartbeat` Socket.IO handler
- [x] 8.3 Add stale-connection sweep logic

## 9. Device status

- [x] 9.1 Implement `GET /api/devices/{device_id}/status`
- [x] 9.2 Add device status tests

## 10. Socket.IO authentication

- [x] 10.1 Accept user JWT (`sub`) and device JWT (`device_id`) on connect
- [x] 10.2 Enter rooms `user:{user_id}` and `device:{device_id}`
- [x] 10.3 Mount Socket.IO ASGI app

## 11. Call signaling

- [x] 11.1 Implement `call:invite` validation and forwarding
- [x] 11.2 Implement `call:accept`, `call:reject`, `call:end` forwarding
- [x] 11.3 Implement `ice:candidate` relay
- [x] 11.4 Implement single-active-call guard (`call:busy`)
- [x] 11.5 Record `CallSession` lifecycle in database

## 12. Whitelist

- [x] 12.1 Verify caller is a contact of the target device before forwarding invite
- [x] 12.2 Emit `call:error` for unauthorized callers
- [x] 12.3 Add whitelist tests

## 13. Deployment and documentation

- [x] 13.1 Add `Dockerfile` and `docker-compose.yml`
- [x] 13.2 Write `README.md` with run/dev/test instructions
- [x] 13.3 Add seed script and WebSocket event schema docs

## 14. Smoke tests and final verification

- [x] 14.1 Add end-to-end smoke test for full call flow
- [x] 14.2 Add health check test
- [x] 14.3 Run full test suite and confirm all pass
