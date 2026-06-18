# Video Call Signaling Server

基于 FastAPI + python-socketio 的视频通话信令后端。

## 本地开发

```bash
cd signaling-server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 快速运行测试（不需要 .env 文件）
SECRET_KEY=test-secret python -m pytest

# 启动开发服务器前复制示例配置并修改
# cp .env.example .env
# uvicorn app.main:socket_app --reload
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
