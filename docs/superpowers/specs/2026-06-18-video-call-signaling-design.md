---
comet_change: video-call-signaling
role: technical-design
canonical_spec: openspec
---

# video-call-signaling Design Doc

## Context

This change builds the backend signaling, identity, and contact-management service for the Raspberry Pi video-call product for elderly users. It must connect the family web caller and the elder Pi device over the internet, handle authentication, contact whitelisting, and WebRTC signaling.

## Goals / Non-Goals

**Goals:**
- Family member accounts with JWT authentication.
- CRUD contacts for each elder device, including avatar and physical button index.
- WebSocket signaling for WebRTC call invite / accept / reject / end / ICE relay.
- Presence heartbeat and online-status query.
- Whitelist enforcement so only contacts can call a device.
- Simple MVP deployment on a VPS, home server, or the Pi itself.

**Non-Goals:**
- Media relay / SFU / MCU. Media is peer-to-peer; TURN is a separate deployment concern.
- Multi-party calls, recording, screen sharing.
- High availability, horizontal scaling, offline message persistence beyond simple status.

## Decisions

### 1. Language & framework: Python 3.11+ + FastAPI + python-socketio
- **Rationale**: Python is well established on Raspberry Pi and makes it easy to share utilities with the elder Pi client. FastAPI gives modern async HTTP APIs with auto-generated OpenAPI docs. `python-socketio` provides rooms, reconnect fallbacks, and broadcasting without building a raw WebSocket protocol from scratch.
- **Alternative considered**: Node.js + Express + Socket.IO. Rejected because the team/user prefers Python for this hardware-oriented product, and the elder client will likely also be Python.

### 2. ORM & database: SQLAlchemy 2.0 + SQLite for MVP, Postgres later
- **Rationale**: SQLAlchemy 2.0 is the standard typed ORM in Python. SQLite requires zero operational setup and is sufficient for a handful of devices. The schema uses portable column types so switching to Postgres later is mostly a connection-string change.

### 3. Real-time channel: Socket.IO namespace `/signaling`
- **Rationale**: Unified event model; easy to group connections by `deviceId` into rooms; built-in reconnect/fallback.
- **Events**:
  - `call:invite` `{ callId, toDeviceId, callerId, callerName, offer }`
  - `call:accept` `{ callId, answer }`
  - `call:reject` `{ callId, reason }`
  - `call:end` `{ callId }`
  - `ice:candidate` `{ callId, candidate }`
  - `presence:heartbeat` `{}`

### 4. Authentication
- HTTP endpoints use JWT Bearer tokens (`Authorization: Bearer <token>`).
- Socket.IO connections authenticate via the `auth.token` field.
- Elder devices authenticate with a dedicated `deviceToken` generated at device registration.
- Passwords hashed with `bcrypt`; tokens signed with HS256 from `SECRET_KEY`.

### 5. Modules

```
signaling-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + Socket.IO mount
│   ├── config.py            # Pydantic Settings from env
│   ├── db.py                # SQLAlchemy engine/session
│   ├── models.py            # User, Device, Contact, CallSession
│   ├── schemas.py           # Pydantic request/response models
│   ├── dependencies.py      # get_db, get_current_user
│   ├── routers/
│   │   ├── auth.py
│   │   ├── devices.py
│   │   └── contacts.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   ├── contact_service.py
│   │   └── call_service.py
│   └── socket/
│       ├── namespace.py     # /signaling event handlers
│       └── manager.py       # room/call state helpers
├── tests/
├── uploads/avatars/
├── alembic/                 # migrations
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

### 6. Avatar storage
- MVP stores avatars on the local filesystem under `uploads/avatars/` and serves them via a static route. Object storage can be swapped in later.

### 7. Deployment
- Single-process ASGI server via `uvicorn`.
- `docker-compose.yml` for local/remote deployment.
- Environment variables: `SECRET_KEY`, `DATABASE_URL`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`, `PORT`.

## Data Flow

1. Family member registers/logs in via HTTP and receives a JWT.
2. Family member creates a `Device` and adds `Contact`s (mapping button index to user).
3. The Pi device connects to Socket.IO with its `deviceToken` and joins room `<deviceId>`.
4. Family member calls elder: emits `call:invite` with `toDeviceId` and WebRTC offer.
5. Server checks that the caller is a contact of `toDeviceId`; if not, emits `call:error`.
6. Server forwards `call:invite` to the device's room.
7. Device emits `call:accept` with the answer; server forwards to caller.
8. Caller and device exchange `ice:candidate` via the server.
9. Either side emits `call:end`; server forwards, updates `CallSession`, and clears active call state.

## Security

- HTTPS in production (TLS terminated by reverse proxy).
- `bcrypt` password hashing.
- JWT access tokens with configurable expiry (default 24h).
- Device ownership checks on all device/contact routes.
- Whitelist enforcement before forwarding any `call:invite`.
- CORS restricted to configured origins.
- Rate limiting on auth endpoints (to be added if public-facing).

## Testing

- **Unit tests**: pytest with in-memory SQLite for services.
- **HTTP integration**: FastAPI `TestClient` for auth, contacts, devices.
- **Socket integration**: `socketio.Client` for invite/accept/end/ICE relay scenarios.
- **Smoke test**: start the server and run a full register → add contact → invite → accept → end flow.

## Risks / Trade-offs

- **SQLite write concurrency**: acceptable for MVP; migration to Postgres later is straightforward.
- **No built-in TURN server**: P2P may fail behind symmetric NATs. Mitigation: design reserves a `turnConfig` field to be pushed to clients; TURN deployed separately.
- **Token leak**: use HTTPS and short-lived tokens; add refresh tokens and device binding in a later change.
- **Python/JavaScript client mismatch**: `python-socketio` on the server is compatible with the official JS Socket.IO client used by the family web app.

## Open Questions

1. Should refresh tokens be implemented now or deferred to a later change?
2. Should the Pi device cache contact avatars locally?
3. Should one family account manage multiple elder devices?
4. Should we provide a raw WebSocket endpoint for clients that cannot use Socket.IO?
