# Verification Report: elder-pi-client

## Summary

| Dimension    | Status                              |
|--------------|-------------------------------------|
| Completeness | 27/27 tasks, 4/4 delta specs        |
| Correctness  | Requirements covered; 1 WARNING     |
| Coherence    | Design decisions followed           |

**Final Assessment**: No critical issues. One warning regarding missing-token UX. Ready for archive with noted improvement.

## Verification Evidence

- Build command: `bash scripts/build.sh` — PASS
- Verify command: `bash scripts/verify.sh` — 43/43 tests PASS
- Client build: `npm run build` in `elder-pi-client/` — PASS
- Client unit tests: `npm run test:unit` in `elder-pi-client/` — 9/9 PASS

## Completeness

- `tasks.md`: all 27 tasks checked `[x]`.
- Delta specs present and reviewed:
  - `specs/pi-device-boot/spec.md`
  - `specs/pi-home-ui/spec.md`
  - `specs/pi-incoming-call/spec.md`
  - `specs/pi-call-session/spec.md`

## Correctness

### pi-device-boot

- Token loaded from `~/.config/elder-pi/device-token` by `launcher.py:116-120`.
- Systemd user service created by `install.sh:21-35`.
- Socket.IO reconnect configured in `signaling.js:29-31`.
- Offline/online indicator handled in `main.js:178-180`.

### pi-home-ui

- Contacts fetched from `/api/devices/:id/contacts` in `main.js:147`.
- Rendered as large buttons sorted by `button_index` in `main.js:48-74` and `styles/main.css`.
- Tap initiates outgoing call in `main.js:76-85`.
- Online/offline status shown via `setStatus` in `ui.js:27-38`.

### pi-incoming-call

- Full-screen incoming UI with caller info in `index.html` and `webrtc.js:126-139`.
- Ringtone played via HTML5 audio in `index.html`.
- Answer/decline handlers in `webrtc.js:141-156`.
- 60-second timeout in `main.js:91-95`.

### pi-call-session

- WebRTC peer connection lifecycle in `webrtc.js:44-87`.
- Local/remote video display in `webrtc.js:39-42`, `61-63`.
- Mute/camera toggle in `webrtc.js:163-173`.
- End call and remote hang-up cleanup in `webrtc.js:158-161`, `181-184`.

### Server-side support

- `signaling-server/app/routers/contacts.py` now accepts device tokens and routes to `list_contacts_for_device`.
- `signaling-server/app/services/contact_service.py:49-57` adds device-scoped contact listing.
- CORS updated to include `127.0.0.1:3000` for local Pi client.

## Issues

### WARNING

- **Missing-token setup screen**: `specs/pi-device-boot/spec.md` requires a setup screen with pairing instructions when the token file is missing. `launcher.py` exits with an error message instead (`launcher.py:117-120`). `main.js:127-130` shows a status message only when the browser config lacks a token, which is unreachable via the launcher path. Recommendation: render a dedicated setup/pairing screen in `index.html` and have `launcher.py` serve the app even when the token is missing, or update the spec to match the current behavior.

## Coherence

- Design Doc decisions followed:
  - Python launcher + local WebView/kiosk (`launcher.py`, `run.sh`, `install.sh`).
  - Pre-configured device token (`~/.config/elder-pi/device-token`).
  - Contacts from `/api/devices/:id/contacts`.
  - systemd user service for auto-start.
  - WebRTC media handling reuses JS patterns from family-web-caller.
- No contradictions detected between delta specs and Design Doc.
