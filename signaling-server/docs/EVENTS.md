# Socket.IO Events

Namespace: `/signaling`

## Connection Auth

```json
{
  "token": "<user-jwt-or-device-jwt>"
}
```

## Client -> Server

### `call:invite`
```json
{
  "callId": "uuid",
  "toDeviceId": "device-uuid",
  "offer": { "type": "offer", "sdp": "..." }
}
```

### `call:accept`
```json
{
  "callId": "uuid",
  "answer": { "type": "answer", "sdp": "..." }
}
```

### `call:reject`
```json
{
  "callId": "uuid",
  "reason": "declined"
}
```

### `call:end`
```json
{ "callId": "uuid" }
```

### `ice:candidate`
```json
{
  "callId": "uuid",
  "candidate": { "candidate": "...", "sdpMid": "0", "sdpMLineIndex": 0 }
}
```

### `presence:heartbeat`
```json
{}
```

## Server -> Client

- `call:invite` — 转发给被叫设备
- `call:accept` — 转发给主叫用户
- `call:reject` — 转发给主叫用户
- `call:end` — 双方转发
- `ice:candidate` — 双方转发
- `call:busy` — 目标设备忙
- `call:error` — 通用错误
