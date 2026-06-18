# Video Call Signaling Server

基于 FastAPI + python-socketio 的视频通话信令后端。

## 本地开发

```bash
cd signaling-server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m pytest
uvicorn app.main:socket_app --reload
```

## Docker 部署

```bash
cp .env.example .env
# 编辑 .env
docker-compose up --build
```

## 主要路由

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/devices`
- `GET /api/devices/{device_id}/status`
- `POST /api/devices/{device_id}/contacts`
- `PATCH /api/contacts/{contact_id}`
- `POST /api/contacts/{contact_id}/avatar`
- Socket.IO namespace `/signaling`
