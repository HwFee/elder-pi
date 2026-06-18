## 1. Project bootstrap

- [ ] 1.1 Create `elder-pi-client/` directory with `index.html`, `src/`, `styles/`, `scripts/`
- [ ] 1.2 Add `package.json` with socket.io-client dependency and build/dev scripts
- [ ] 1.3 Add basic fullscreen CSS for Pi touchscreen (large buttons, no scrollbars)

## 2. Device boot and token loader

- [ ] 2.1 Implement `src/config.js` to read `device_token` from localStorage fallback or injected config
- [ ] 2.2 Add Python launcher `launcher.py` that reads `~/.config/elder-pi/device-token` and serves files
- [ ] 2.3 Add `install.sh` to create systemd user service for auto-start
- [ ] 2.4 Add `run.sh` for local development

## 3. Signaling client

- [ ] 3.1 Add `src/signaling.js` to connect to `/signaling` with device token
- [ ] 3.2 Handle reconnect and offline/online indicators
- [ ] 3.3 Emit and handle `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`

## 4. Home UI

- [ ] 4.1 Fetch contacts from `/api/devices/:id/contacts` on connect
- [ ] 4.2 Render contacts as large buttons ordered by `button_index`
- [ ] 4.3 Tap a contact to create an offer and emit `call_invite`
- [ ] 4.4 Show outgoing call screen while waiting

## 5. Incoming call UI

- [ ] 5.1 Show full-screen incoming call with caller name/avatar and answer/decline buttons
- [ ] 5.2 Play ringtone on `call:invite`
- [ ] 5.3 Implement answer flow: create answer, emit `call_accept`, switch to active call
- [ ] 5.4 Implement decline flow: emit `call_reject`, return home
- [ ] 5.5 Auto-decline after 60 seconds timeout

## 6. WebRTC call session

- [ ] 6.1 Add `src/webrtc.js` for `RTCPeerConnection` lifecycle (reuse patterns from family-web-caller)
- [ ] 6.2 Display local video overlay and remote video full-screen
- [ ] 6.3 Add mute, camera-off, and end-call buttons
- [ ] 6.4 Return to home on remote `call:end` or local hang-up

## 7. Deployment and verification

- [ ] 7.1 Add README with install, token setup, and run instructions
- [ ] 7.2 Build project successfully
- [ ] 7.3 Manually smoke-test boot, home, incoming call, and outgoing call against backend
- [ ] 7.4 Add minimal unit/E2E tests if feasible (e.g., signaling event routing)
