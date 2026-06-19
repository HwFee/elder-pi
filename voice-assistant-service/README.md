# Voice Assistant Service

AI-powered voice assistant for elder-pi system.

## 功能

- 语音识别（STT）：将老人语音转为文字
- AI 理解：判断意图（打电话/发消息/查消息）
- 语音合成（TTS）：将 AI 回复转为语音
- 多轮对话：信息不完整时自动追问
- 语音消息：实时收发语音消息

## 本地开发

```bash
cd voice-assistant-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 启动
uvicorn app.main:app --reload --port 8001
```

## Docker 部署

```bash
# 在仓库根目录
docker-compose up --build voice-assistant
```

## API 文档

启动后访问: http://localhost:8001/docs
