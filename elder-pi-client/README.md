# elder-pi-client

树莓派老人端视频通话客户端。

## 功能

- 开机自启动，通电即用。
- 大按钮显示联系人，一键呼叫家属。
- 来电全屏响铃，一键接听/拒接。
- WebRTC 视频通话，支持静音、关闭摄像头、挂断。
- 离线自动重连。

## 目录结构

```
elder-pi-client/
├── index.html          # 主界面
├── styles/main.css     # 全屏大屏样式
├── src/                # JS 模块
├── launcher.py         # Python 启动器（静态服务 + token 注入）
├── run.sh              # 开发运行脚本
├── install.sh          # 安装 systemd 自启服务
└── README.md
```

## 安装与运行

### 1. 准备设备 token

在家属网页端 (`family-web-caller`) 添加设备后，会生成一个 device token。将其写入树莓派：

```bash
mkdir -p ~/.config/elder-pi
echo "YOUR_DEVICE_TOKEN" > ~/.config/elder-pi/device-token
chmod 600 ~/.config/elder-pi/device-token
```

### 2. 安装依赖

```bash
cd elder-pi-client
npm install
```

### 3. 开发运行

```bash
./run.sh
```

然后在本机浏览器打开 `http://127.0.0.1:3000/`。

### 4. 生产部署（开机自启）

```bash
./install.sh
systemctl --user start elder-pi-client
```

## 配置

启动器默认连接后端 `http://127.0.0.1:8000`。可通过参数修改：

```bash
python3 launcher.py --backend http://192.168.1.10:8000 --port 3000
```

## 构建静态文件

```bash
npm run build
```

产物输出到 `dist/`，可被任何静态服务器托管。

## 测试

```bash
npm run test:unit
```
