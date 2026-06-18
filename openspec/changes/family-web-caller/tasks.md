## 1. Project bootstrap

- [ ] 1.1 Initialize Vite project under `family-web-caller/`
- [ ] 1.2 Add `index.html`, `dashboard.html`, `call.html`
- [ ] 1.3 Add basic CSS and shared layout

## 2. Authentication

- [ ] 2.1 Implement login page (`index.html`)
- [ ] 2.2 Add `api.js` wrapper for backend HTTP calls
- [ ] 2.3 Add `auth.js` for JWT storage/retrieval/logout
- [ ] 2.4 Protect dashboard and call pages by redirecting unauthenticated users

## 3. Dashboard

- [ ] 3.1 Fetch and render device list
- [ ] 3.2 Fetch and render contacts for selected device
- [ ] 3.3 Add contact form (create/update)
- [ ] 3.4 Add contact delete with confirmation
- [ ] 3.5 Add avatar upload preview and submit

## 4. Signaling client

- [ ] 4.1 Add `signaling.js` using `socket.io-client`
- [ ] 4.2 Connect with user JWT and handle reconnect
- [ ] 4.3 Emit and handle `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`
- [ ] 4.4 Handle `call:busy` and `call:error`

## 5. WebRTC call UI

- [ ] 5.1 Add `webrtc.js` wrapping `RTCPeerConnection`
- [ ] 5.2 Create offer on outgoing call
- [ ] 5.3 Create answer on incoming call
- [ ] 5.4 Display local and remote video
- [ ] 5.5 Add mute and camera-off toggles
- [ ] 5.6 Add end-call button

## 6. Deployment

- [ ] 6.1 Add `Dockerfile` with nginx static server
- [ ] 6.2 Add `nginx.conf` to proxy API/WebSocket to backend
- [ ] 6.3 Update root `docker-compose.yml` to include family-web-caller
- [ ] 6.4 Add README with dev/build/run instructions

## 7. Verification

- [ ] 7.1 Build project successfully
- [ ] 7.2 Manually smoke-test login, dashboard, call flow against backend
- [ ] 7.3 Add Playwright or basic UI tests for critical paths
- [ ] 7.4 Run full verification
