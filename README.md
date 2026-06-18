# Family Web Caller

家庭端 Web 视频通话客户端，配套 `signaling-server` 使用。

## 本地开发

```bash
cd family-web-caller
npm install
npm run dev
```

确保 `signaling-server` 已运行在 `http://localhost:8000`。

## 构建

```bash
npm run build
```

## 测试

```bash
npm run test:unit
npm run test:e2e
```

## Docker 部署

在仓库根目录：

```bash
cp signaling-server/.env.example .env
# 编辑 .env
docker-compose up --build
```

访问 `http://localhost`。
