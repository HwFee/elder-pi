---
comet_change: family-web-caller
role: technical-design
canonical_spec: openspec
---

# family-web-caller Design Doc

## Context

This change builds the family-facing web client for the Raspberry Pi video-call product. The backend `video-call-signaling` already provides authentication, device/contact management, presence, and WebRTC signaling. This client consumes those APIs over HTTP and Socket.IO.

## Goals / Non-Goals

**Goals:**
- Login page using backend JWT.
- Dashboard for device/contact management with avatar upload.
- Video call UI with outgoing/incoming call support.
- WebRTC P2P media connection.
- Static deployment via nginx + Docker.

**Non-Goals:**
- Multi-party calls, chat, screen sharing.
- Native mobile app.
- Self-hosted TURN server.

## Decisions

### 1. Stack: Vite + Vanilla JS + socket.io-client
- **Rationale**: Simplest viable stack; no framework lock-in; easy to deploy as static files.
- **Alternatives**: Vue/React. Rejected as overkill for this MVP.

### 2. Page-based routing
- `index.html` login, `dashboard.html` management, `call.html` active call.
- **Rationale**: Keeps each page focused; no SPA router needed.

### 3. Module responsibilities
```
family-web-caller/src/
├── api.js          # fetch wrappers for backend REST
├── auth.js         # JWT storage, login/logout, auth guards
├── signaling.js    # socket.io-client connection and event routing
├── webrtc.js       # RTCPeerConnection lifecycle
├── ui.js           # DOM helpers
└── main.js         # page bootstrap
```

### 4. WebRTC flow
1. Outgoing: getUserMedia → createOffer → setLocalDescription → emit `call:invite`.
2. Incoming: receive `call:invite` → getUserMedia → createAnswer → setLocalDescription → emit `call:accept`.
3. Both: on `ice:candidate`, emit to server; on receive, `addIceCandidate`.
4. End: emit/receive `call:end`, stop tracks, close peer connection.

### 5. Deployment
- `Dockerfile` uses nginx to serve `dist/`.
- `nginx.conf` proxies `/api` and `/socket.io` to the signaling server.
- Root `docker-compose.yml` adds the `family-web-caller` service.

## Risks / Trade-offs

- **Browser compatibility**: Target modern browsers; Safari may need polyfills or constraints.
- **No state management library**: Keep modules small to avoid spaghetti code.
- **P2P NAT traversal**: TURN config required for restrictive networks.

## Open Questions

1. Should the call page open in a modal or a new tab?
2. Should we show a call timer?
3. Should we support multiple elder devices in one family account?
