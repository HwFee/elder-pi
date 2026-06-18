---
change: elder-pi-client
design-doc: docs/superpowers/specs/2026-06-18-elder-pi-client-design.md
base-ref: 8d3debf14fab5ad4ef099808531daca4b0ff59ad
archived-with: 2026-06-18-elder-pi-client
---

# elder-pi-client Implementation Plan

## 1. Project bootstrap

- [x] 1.1 Create `elder-pi-client/` directory with `index.html`, `src/`, `styles/`, `scripts/`
- [x] 1.2 Add `package.json` with socket.io-client dependency and build/dev scripts
- [x] 1.3 Add basic fullscreen CSS for Pi touchscreen (large buttons, no scrollbars)

## 2. Device boot and token loader

- [x] 2.1 Implement `src/config.js` to read `device_token` from localStorage fallback or injected config
- [x] 2.2 Add Python launcher `launcher.py` that reads `~/.config/elder-pi/device-token` and serves files
- [x] 2.3 Add `install.sh` to create systemd user service for auto-start
- [x] 2.4 Add `run.sh` for local development

## 3. Signaling client

- [x] 3.1 Add `src/signaling.js` to connect to `/signaling` with device token
- [x] 3.2 Handle reconnect and offline/online indicators
- [x] 3.3 Emit and handle `call:invite`, `call:accept`, `call:reject`, `call:end`, `ice:candidate`

## 4. Home UI

- [x] 4.1 Fetch contacts from `/api/devices/:id/contacts` on connect
- [x] 4.2 Render contacts as large buttons ordered by `button_index`
- [x] 4.3 Tap a contact to create an offer and emit `call_invite`
- [x] 4.4 Show outgoing call screen while waiting

## 5. Incoming call UI

- [x] 5.1 Show full-screen incoming call with caller name/avatar and answer/decline buttons
- [x] 5.2 Play ringtone on `call:invite`
- [x] 5.3 Implement answer flow: create answer, emit `call_accept`, switch to active call
- [x] 5.4 Implement decline flow: emit `call_reject`, return home
- [x] 5.5 Auto-decline after 60 seconds timeout

## 6. WebRTC call session

- [x] 6.1 Add `src/webrtc.js` for `RTCPeerConnection` lifecycle (reuse patterns from family-web-caller)
- [x] 6.2 Display local video overlay and remote video full-screen
- [x] 6.3 Add mute, camera-off, and end-call buttons
- [x] 6.4 Return to home on remote `call:end` or local hang-up

## 7. Deployment and verification

- [x] 7.1 Add README with install, token setup, and run instructions
- [x] 7.2 Build project successfully
- [x] 7.3 Manually smoke-test boot, home, incoming call, and outgoing call against backend
- [x] 7.4 Add minimal unit/E2E tests if feasible
