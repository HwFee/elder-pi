## 1. Project bootstrap

- [x] 1.1 Initialize Vite project under `family-web-caller/`
- [x] 1.2 Add `index.html`, `dashboard.html`, `call.html`
- [x] 1.3 Add basic CSS and shared layout

## 2. Authentication

- [x] 2.1 Implement login page (`index.html`)
- [x] 2.2 Add `api.js` wrapper for backend HTTP calls
- [x] 2.3 Add `auth.js` for JWT storage/retrieval/logout
- [x] 2.4 Protect dashboard and call pages by redirecting unauthenticated users

## 3. Dashboard

- [x] 3.1 Fetch and render device list
- [x] 3.2 Fetch and render contacts for selected device
- [x] 3.3 Add contact form (create/update)
- [x] 3.4 Add contact delete with confirmation
- [x] 3.5 Add avatar upload preview and submit

## 4. Signaling client

- [x] 4.1 Add `signaling.js` using `socket.io-client`
- [x] 4.2 Connect with user JWT and handle reconnect
- [x] 4.3 Emit and handle `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`
- [x] 4.4 Handle `call:busy` and `call:error`

## 5. WebRTC call UI

- [x] 5.1 Add `webrtc.js` wrapping `RTCPeerConnection`
- [x] 5.2 Create offer on outgoing call
- [x] 5.3 Create answer on incoming call
- [x] 5.4 Display local and remote video
- [x] 5.5 Add mute and camera-off toggles
- [x] 5.6 Add end-call button

## 6. Deployment

- [x] 6.1 Add `Dockerfile` with nginx static server
- [x] 6.2 Add `nginx.conf` to proxy API/WebSocket to backend
- [x] 6.3 Update root `docker-compose.yml` to include family-web-caller
- [x] 6.4 Add README with dev/build/run instructions

## 7. Verification

- [x] 7.1 Build project successfully
- [x] 7.2 Manually smoke-test login, dashboard, call flow against backend
- [x] 7.3 Add Playwright or basic UI tests for critical paths
- [x] 7.4 Run full verification
