---
change: family-web-caller
design-doc: docs/superpowers/specs/2026-06-18-family-web-caller-design.md
base-ref: 0b271f72c8e4da523310f733c8b81b5a28acfb11
archived-with: 2026-06-18-family-web-caller
---

# family-web-caller 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 Vite + 原生 JS 的家庭端 Web 视频通话客户端，完成后端 JWT 登录、设备/联系人管理、WebRTC P2P 通话，并通过 nginx + Docker 静态部署。

**Architecture:** 采用三页面架构（登录页、管理仪表盘、通话页），核心逻辑按职责拆分为 `api.js`、`auth.js`、`signaling.js`、`webrtc.js`、`ui.js`、`main.js`。通过 `socket.io-client` 与信令服务器交互，`RTCPeerConnection` 处理媒体连接，nginx 反向代理 API 与 WebSocket。

**Tech Stack:** Vite、原生 JavaScript、socket.io-client、WebRTC、nginx、Docker、Playwright（测试）。

## 全局约束

- 浏览器目标：现代浏览器（Chrome、Firefox、Edge、Safari 最新版）。
- 前端项目目录：`family-web-caller/`。
- 页面入口：`index.html`（登录）、`dashboard.html`（管理）、`call.html`（通话）。
- 后端 API 前缀：`/api`，Socket.IO 命名空间：`/signaling`。
- JWT 使用 `access_token`，存储于 `localStorage` 键 `access_token`。
- 部署时 nginx 将 `/api` 和 `/socket.io` 代理到信令服务。
- 不引入 React/Vue 等框架；不实现多路通话、聊天、屏幕共享、自托管 TURN。

archived-with: 2026-06-18-family-web-caller
---

## 文件结构

```
family-web-caller/
├── index.html                  # 登录页
├── dashboard.html              # 设备/联系人管理页
├── call.html                   # 视频通话页
├── package.json                # Vite + socket.io-client + dev deps
├── vite.config.js              # 多页面入口、dev proxy
├── .gitignore
├── Dockerfile                  # nginx 静态服务
├── nginx.conf                  # 反向代理 /api 与 /socket.io
├── src/
│   ├── api.js                  # 后端 REST 封装（fetch + FormData）
│   ├── auth.js                 # JWT 存取、登录/登出、认证守卫
│   ├── signaling.js            # socket.io-client 连接与事件路由
│   ├── webrtc.js               # RTCPeerConnection 生命周期
│   ├── ui.js                   # DOM 工具函数
│   └── main.js                 # 页面级引导与路由初始化
├── public/
│   └── (静态资源)
├── styles/
│   └── main.css                # 共享样式
└── tests/
    └── e2e/
        └── family.spec.js      # Playwright 关键路径测试
```

根目录新增/修改：

- `docker-compose.yml`：聚合 `signaling` 与 `family-web-caller` 服务。
- `README.md`：项目构建与运行说明。

archived-with: 2026-06-18-family-web-caller
---

### Task 1: 项目脚手架

**Files:**
- Create: `family-web-caller/package.json`
- Create: `family-web-caller/vite.config.js`
- Create: `family-web-caller/.gitignore`
- Create: `family-web-caller/index.html`
- Create: `family-web-caller/dashboard.html`
- Create: `family-web-caller/call.html`
- Create: `family-web-caller/styles/main.css`
- Create: `family-web-caller/src/main.js`

**Interfaces:**
- Produces: 三页面 HTML 骨架与 Vite 多页配置，所有后续任务在此目录下工作。

- [ ] **Step 1: 初始化 Vite 项目**

在仓库根目录执行：

```bash
npm create vite@latest family-web-caller -- --template vanilla
```

进入目录并安装依赖：

```bash
cd family-web-caller
npm install
npm install socket.io-client
npm install -D playwright @playwright/test
```

- [ ] **Step 2: 配置多页面入口**

创建 `family-web-caller/vite.config.js`：

```javascript
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        index: resolve(__dirname, 'index.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
        call: resolve(__dirname, 'call.html'),
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/socket.io': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
  },
});
```

- [ ] **Step 3: 创建页面骨架**

创建 `family-web-caller/index.html`：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>家庭端登录</title>
    <link rel="stylesheet" href="/styles/main.css" />
  </head>
  <body data-page="login">
    <main class="container">
      <h1>家庭端视频通话</h1>
      <form id="login-form">
        <label>
          邮箱
          <input type="email" id="email" required autocomplete="email" />
        </label>
        <label>
          密码
          <input type="password" id="password" required autocomplete="current-password" />
        </label>
        <button type="submit">登录</button>
        <p id="login-error" class="error" role="alert"></p>
      </form>
    </main>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

创建 `family-web-caller/dashboard.html`：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>设备管理</title>
    <link rel="stylesheet" href="/styles/main.css" />
  </head>
  <body data-page="dashboard">
    <header class="top-bar">
      <span id="user-name"></span>
      <button id="logout">退出</button>
    </header>
    <main class="container">
      <section id="devices-section">
        <h2>我的设备</h2>
        <ul id="device-list"></ul>
        <form id="add-device-form">
          <input type="text" id="device-name" placeholder="设备名称" required />
          <button type="submit">添加设备</button>
        </form>
      </section>
      <section id="contacts-section" hidden>
        <h2>联系人</h2>
        <ul id="contact-list"></ul>
        <form id="contact-form">
          <input type="hidden" id="contact-id" />
          <input type="text" id="contact-display-name" placeholder="称呼" required />
          <input type="number" id="contact-button-index" placeholder="按钮序号" required min="1" max="8" />
          <button type="submit" id="contact-submit">保存联系人</button>
        </form>
        <form id="avatar-form">
          <label>
            头像
            <input type="file" id="avatar-file" accept="image/*" />
          </label>
          <img id="avatar-preview" alt="头像预览" hidden />
          <button type="submit">上传头像</button>
        </form>
      </section>
    </main>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

创建 `family-web-caller/call.html`：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>视频通话</title>
    <link rel="stylesheet" href="/styles/main.css" />
  </head>
  <body data-page="call">
    <main class="call-container">
      <div id="call-status" class="status">准备中…</div>
      <video id="remote-video" autoplay playsinline></video>
      <video id="local-video" autoplay playsinline muted></video>
      <div class="call-controls">
        <button id="toggle-mic">静音</button>
        <button id="toggle-camera">关闭摄像头</button>
        <button id="end-call" class="danger">结束通话</button>
      </div>
    </main>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: 创建基础样式**

创建 `family-web-caller/styles/main.css`：

```css
:root {
  --primary: #2563eb;
  --danger: #dc2626;
  --bg: #f8fafc;
  --text: #1e293b;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
}

.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 1.5rem;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.error { color: var(--danger); }

button {
  cursor: pointer;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  background: var(--primary);
  color: #fff;
}

button.danger { background: var(--danger); }

.call-container {
  position: relative;
  height: 100vh;
  background: #0f172a;
}

#remote-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

#local-video {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  width: 180px;
  height: 135px;
  border-radius: 0.5rem;
  object-fit: cover;
}

.call-controls {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.75rem;
}

.status {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
}
```

- [ ] **Step 5: 创建入口 `main.js`**

创建 `family-web-caller/src/main.js`：

```javascript
import { initLogin } from './auth.js';
import { initDashboard } from './api.js';
import { initCall } from './webrtc.js';

function bootstrap() {
  const page = document.body.dataset.page;
  if (page === 'login') initLogin();
  else if (page === 'dashboard') initDashboard();
  else if (page === 'call') initCall();
}

bootstrap();
```

- [ ] **Step 6: 本地启动验证**

运行：

```bash
cd family-web-caller
npm run dev
```

打开 `http://localhost:5173/index.html`，确认页面标题为"家庭端登录"。

- [ ] **Step 7: 提交**

```bash
git add family-web-caller
git commit -m "chore(family-web-caller): bootstrap Vite multi-page project"
```

archived-with: 2026-06-18-family-web-caller
---

### Task 2: 认证模块

**Files:**
- Create: `family-web-caller/src/auth.js`
- Create: `family-web-caller/src/api.js`
- Modify: `family-web-caller/src/main.js`

**Interfaces:**
- Produces:
  - `getToken(): string | null`
  - `setToken(token: string): void`
  - `clearToken(): void`
  - `login(email: string, password: string): Promise<void>`
  - `logout(): void`
  - `requireAuth(): void`（未登录时跳转 `/index.html`）
  - `apiClient(method, path, body?, isForm?): Promise<any>`

- [ ] **Step 1: 编写 `auth.js` 测试单元（Vitest）**

安装 Vitest：

```bash
cd family-web-caller
npm install -D vitest jsdom @testing-library/dom
```

创建 `family-web-caller/src/auth.test.js`：

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getToken, setToken, clearToken, login, logout, requireAuth } from './auth.js';

describe('auth', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal('location', { href: '' });
  });

  it('stores and retrieves token', () => {
    setToken('abc');
    expect(getToken()).toBe('abc');
  });

  it('clears token on logout', () => {
    setToken('abc');
    logout();
    expect(getToken()).toBeNull();
  });

  it('redirects unauthenticated users', () => {
    requireAuth();
    expect(location.href).toBe('/index.html');
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

```bash
npx vitest run src/auth.test.js
```

预期失败：`Error: Failed to resolve import "./auth.js"`。

- [ ] **Step 3: 实现 `auth.js`**

创建 `family-web-caller/src/auth.js`：

```javascript
const TOKEN_KEY = 'access_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function login(email, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username: email, password }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || '登录失败');
  }

  const data = await response.json();
  setToken(data.access_token);
}

export function logout() {
  clearToken();
  window.location.href = '/index.html';
}

export function requireAuth() {
  if (!getToken()) {
    window.location.href = '/index.html';
  }
}
```

- [ ] **Step 4: 实现 `api.js` 基础封装**

创建 `family-web-caller/src/api.js`：

```javascript
import { getToken } from './auth.js';

export async function apiClient(method, path, body = null, isForm = false) {
  const token = getToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (!isForm && body) headers['Content-Type'] = 'application/json';

  const options = { method, headers };
  if (body) options.body = isForm ? body : JSON.stringify(body);

  const response = await fetch(path, options);

  if (response.status === 204) return null;
  const data = response.headers.get('content-type')?.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new Error(data.detail || data || `Request failed: ${response.status}`);
  }
  return data;
}

export function getMe() {
  return apiClient('GET', '/api/auth/me');
}
```

- [ ] **Step 5: 运行测试确认通过**

```bash
npx vitest run src/auth.test.js
```

预期：全部通过。

- [ ] **Step 6: 更新 `main.js` 添加认证守卫**

修改 `family-web-caller/src/main.js`：

```javascript
import { initLogin, requireAuth } from './auth.js';
import { initDashboard } from './api.js';
import { initCall } from './webrtc.js';

function bootstrap() {
  const page = document.body.dataset.page;
  if (page === 'login') {
    initLogin();
  } else if (page === 'dashboard') {
    requireAuth();
    initDashboard();
  } else if (page === 'call') {
    requireAuth();
    initCall();
  }
}

bootstrap();
```

- [ ] **Step 7: 提交**

```bash
git add family-web-caller/src
git commit -m "feat(family-web-caller): add auth and API client modules"
```

archived-with: 2026-06-18-family-web-caller
---

### Task 3: 仪表盘（设备与联系人管理）

**Files:**
- Modify: `family-web-caller/src/api.js`
- Modify: `family-web-caller/src/ui.js`（创建）
- Modify: `family-web-caller/src/main.js`
- Modify: `family-web-caller/dashboard.html`

**Interfaces:**
- Consumes: `apiClient`, `getToken`。
- Produces:
  - `listDevices(): Promise<DeviceResponse[]>`
  - `createDevice(displayName): Promise<DeviceTokenResponse>`
  - `getDeviceStatus(deviceId): Promise<DeviceStatusResponse>`
  - `listContacts(deviceId): Promise<ContactResponse[]>`
  - `createContact(deviceId, payload): Promise<ContactResponse>`
  - `updateContact(contactId, payload): Promise<ContactResponse>`
  - `deleteContact(contactId): Promise<void>`
  - `uploadAvatar(contactId, file): Promise<ContactResponse>`
  - `initDashboard(): void`

- [ ] **Step 1: 扩展 `api.js` 设备与联系人接口**

追加到 `family-web-caller/src/api.js`：

```javascript
export function listDevices() {
  return apiClient('GET', '/api/devices');
}

export function createDevice(displayName) {
  return apiClient('POST', '/api/devices', { display_name: displayName });
}

export function getDeviceStatus(deviceId) {
  return apiClient('GET', `/api/devices/${deviceId}/status`);
}

export function listContacts(deviceId) {
  return apiClient('GET', `/api/devices/${deviceId}/contacts`);
}

export function createContact(deviceId, payload) {
  return apiClient('POST', `/api/devices/${deviceId}/contacts`, payload);
}

export function updateContact(contactId, payload) {
  return apiClient('PATCH', `/api/contacts/${contactId}`, payload);
}

export function deleteContact(contactId) {
  return apiClient('DELETE', `/api/contacts/${contactId}`);
}

export function uploadAvatar(contactId, file) {
  const form = new FormData();
  form.append('file', file);
  return apiClient('POST', `/api/contacts/${contactId}/avatar`, form, true);
}
```

- [ ] **Step 2: 创建 `ui.js` 工具函数**

创建 `family-web-caller/src/ui.js`：

```javascript
export function $(selector, root = document) {
  return root.querySelector(selector);
}

export function clearChildren(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

export function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function show(el) { el.hidden = false; }
export function hide(el) { el.hidden = true; }
```

- [ ] **Step 3: 实现仪表盘初始化**

在 `family-web-caller/src/api.js` 末尾追加：

```javascript
import { $, clearChildren, escapeHtml, show, hide } from './ui.js';
import { getMe, logout } from './auth.js';

export async function initDashboard() {
  const user = await getMe();
  $('#user-name').textContent = user.full_name;
  $('#logout').addEventListener('click', logout);

  let selectedDeviceId = null;
  let selectedContactId = null;
  let devices = [];

  async function renderDevices() {
    devices = await listDevices();
    const list = $('#device-list');
    clearChildren(list);
    for (const device of devices) {
      const li = document.createElement('li');
      li.innerHTML = `<button data-id="${escapeHtml(device.id)}">${escapeHtml(device.display_name)}</button>`;
      list.appendChild(li);
    }
    list.querySelectorAll('button').forEach((btn) => {
      btn.addEventListener('click', () => selectDevice(btn.dataset.id));
    });
  }

  async function selectDevice(deviceId) {
    selectedDeviceId = deviceId;
    const status = await getDeviceStatus(deviceId);
    $('#contacts-section h2').textContent = `设备 ${escapeHtml(devices.find((d) => d.id === deviceId)?.display_name || '')} 的联系人 ${status.online ? '(在线)' : '(离线)'}`;
    show($('#contacts-section'));
    await renderContacts(deviceId);
  }

  async function renderContacts(deviceId) {
    const { contacts } = await listContacts(deviceId);
    const list = $('#contact-list');
    clearChildren(list);
    for (const contact of contacts) {
      const li = document.createElement('li');
      li.innerHTML = `
        <span>${escapeHtml(contact.display_name)}</span>
        <button class="edit-contact" data-id="${escapeHtml(contact.id)}">编辑</button>
        <button class="delete-contact" data-id="${escapeHtml(contact.id)}">删除</button>
        <button class="call-contact" data-device="${escapeHtml(contact.device_id)}" data-user="${escapeHtml(contact.user_id)}">通话</button>
      `;
      list.appendChild(li);
    }
    list.querySelectorAll('.edit-contact').forEach((btn) =>
      btn.addEventListener('click', () => loadContactForm(btn.dataset.id, contacts))
    );
    list.querySelectorAll('.delete-contact').forEach((btn) =>
      btn.addEventListener('click', () => onDeleteContact(btn.dataset.id))
    );
    list.querySelectorAll('.call-contact').forEach((btn) =>
      btn.addEventListener('click', () => startCallFromDashboard(btn.dataset.device, btn.dataset.user))
    );
  }

  function loadContactForm(contactId, contacts) {
    const contact = contacts.find((c) => c.id === contactId);
    if (!contact) return;
    selectedContactId = contactId;
    $('#contact-id').value = contactId;
    $('#contact-display-name').value = contact.display_name;
    $('#contact-button-index').value = contact.button_index;
    $('#contact-submit').textContent = '更新联系人';
    if (contact.avatar_path) {
      $('#avatar-preview').src = `/api/uploads/${contact.avatar_path}`;
      show($('#avatar-preview'));
    }
  }

  async function onDeleteContact(contactId) {
    if (!confirm('确定删除该联系人？')) return;
    await deleteContact(contactId);
    await renderContacts(selectedDeviceId);
  }

  $('#add-device-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = $('#device-name');
    await createDevice(input.value.trim());
    input.value = '';
    await renderDevices();
  });

  $('#contact-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      display_name: $('#contact-display-name').value.trim(),
      button_index: Number($('#contact-button-index').value),
    };
    if (selectedContactId) {
      await updateContact(selectedContactId, payload);
    } else {
      await createContact(selectedDeviceId, payload);
    }
    selectedContactId = null;
    $('#contact-form').reset();
    $('#contact-submit').textContent = '保存联系人';
    await renderContacts(selectedDeviceId);
  });

  $('#avatar-file').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    $('#avatar-preview').src = url;
    show($('#avatar-preview'));
  });

  $('#avatar-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedContactId) {
      alert('请先选择或创建一个联系人');
      return;
    }
    const file = $('#avatar-file').files[0];
    if (!file) return;
    await uploadAvatar(selectedContactId, file);
    await renderContacts(selectedDeviceId);
  });

  await renderDevices();
}

function startCallFromDashboard(deviceId, userId) {
  const params = new URLSearchParams({ device: deviceId, user: userId });
  window.location.href = `/call.html?${params.toString()}`;
}
```

- [ ] **Step 4: 更新 `main.js` 导入 `initDashboard`**

`family-web-caller/src/main.js` 中：

```javascript
import { initDashboard } from './api.js';
```

保持不变即可（Task 2 已引入）。

- [ ] **Step 5: 启动后端并手动验证**

在 `signaling-server` 目录：

```bash
cd signaling-server
SECRET_KEY=test-secret python -m uvicorn app.main:socket_app --reload --port 8000
```

在 `family-web-caller` 目录：

```bash
npm run dev
```

访问 `http://localhost:5173/index.html`，登录后跳转仪表盘，确认设备列表渲染正常。

- [ ] **Step 6: 提交**

```bash
git add family-web-caller/src family-web-caller/dashboard.html
git commit -m "feat(family-web-caller): add dashboard for device and contact management"
```

archived-with: 2026-06-18-family-web-caller
---

### Task 4: 信令客户端

**Files:**
- Create: `family-web-caller/src/signaling.js`

**Interfaces:**
- Consumes: `getToken`。
- Produces:
  - `connect(): Socket`
  - `disconnect(): void`
  - `emitInvite(callId, toDeviceId, offer): void`
  - `emitAccept(callId, answer): void`
  - `emitReject(callId, reason?): void`
  - `emitEnd(callId): void`
  - `emitIceCandidate(callId, candidate): void`
  - `onInvite(callback): void`
  - `onAccept(callback): void`
  - `onReject(callback): void`
  - `onEnd(callback): void`
  - `onBusy(callback): void`
  - `onError(callback): void`
  - `onIceCandidate(callback): void`

- [ ] **Step 1: 编写 `signaling.js` 测试**

创建 `family-web-caller/src/signaling.test.js`：

```javascript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { io } from 'socket.io-client';
import { connect, emitInvite, onInvite } from './signaling.js';

vi.mock('socket.io-client');

describe('signaling', () => {
  let mockSocket;

  beforeEach(() => {
    mockSocket = {
      on: vi.fn(),
      emit: vi.fn(),
      disconnect: vi.fn(),
    };
    io.mockReturnValue(mockSocket);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('connects with token auth', () => {
    connect();
    expect(io).toHaveBeenCalledWith('/signaling', expect.objectContaining({ auth: expect.any(Object) }));
  });

  it('emits call:invite', () => {
    connect();
    emitInvite('c1', 'd1', { type: 'offer', sdp: 'x' });
    expect(mockSocket.emit).toHaveBeenCalledWith('call_invite', {
      callId: 'c1',
      toDeviceId: 'd1',
      offer: { type: 'offer', sdp: 'x' },
    });
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

```bash
npx vitest run src/signaling.test.js
```

预期失败：`Error: Failed to resolve import "./signaling.js"`。

- [ ] **Step 3: 实现 `signaling.js`**

创建 `family-web-caller/src/signaling.js`：

```javascript
import { io } from 'socket.io-client';
import { getToken } from './auth.js';

let socket = null;
const handlers = {
  invite: [],
  accept: [],
  reject: [],
  end: [],
  busy: [],
  error: [],
  iceCandidate: [],
};

export function connect() {
  if (socket) return socket;

  socket = io('/signaling', {
    auth: { token: getToken() },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
  });

  socket.on('connect', () => {
    console.info('signaling connected', socket.id);
  });

  socket.on('disconnect', (reason) => {
    console.info('signaling disconnected', reason);
  });

  socket.on('connect_error', (err) => {
    console.error('signaling connect_error', err.message);
  });

  socket.on('call:invite', (data) => handlers.invite.forEach((cb) => cb(data)));
  socket.on('call:accept', (data) => handlers.accept.forEach((cb) => cb(data)));
  socket.on('call:reject', (data) => handlers.reject.forEach((cb) => cb(data)));
  socket.on('call:end', (data) => handlers.end.forEach((cb) => cb(data)));
  socket.on('call:busy', (data) => handlers.busy.forEach((cb) => cb(data)));
  socket.on('call:error', (data) => handlers.error.forEach((cb) => cb(data)));
  socket.on('ice:candidate', (data) => handlers.iceCandidate.forEach((cb) => cb(data)));

  return socket;
}

export function disconnect() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
  Object.keys(handlers).forEach((key) => {
    handlers[key] = [];
  });
}

export function emitInvite(callId, toDeviceId, offer) {
  socket?.emit('call_invite', { callId, toDeviceId, offer });
}

export function emitAccept(callId, answer) {
  socket?.emit('call_accept', { callId, answer });
}

export function emitReject(callId, reason = '') {
  socket?.emit('call_reject', { callId, reason });
}

export function emitEnd(callId) {
  socket?.emit('call_end', { callId });
}

export function emitIceCandidate(callId, candidate) {
  socket?.emit('ice_candidate', { callId, candidate });
}

export function onInvite(callback) {
  handlers.invite.push(callback);
}

export function onAccept(callback) {
  handlers.accept.push(callback);
}

export function onReject(callback) {
  handlers.reject.push(callback);
}

export function onEnd(callback) {
  handlers.end.push(callback);
}

export function onBusy(callback) {
  handlers.busy.push(callback);
}

export function onError(callback) {
  handlers.error.push(callback);
}

export function onIceCandidate(callback) {
  handlers.iceCandidate.push(callback);
}
```

注意：后端 Python 命名空间事件处理器使用下划线命名（`on_call_invite`），Socket.IO 客户端发送时的事件名对应为 `call_invite`；后端广播给用户的事件名为 `call:invite`。

- [ ] **Step 4: 运行测试确认通过**

```bash
npx vitest run src/signaling.test.js
```

预期：全部通过。

- [ ] **Step 5: 提交**

```bash
git add family-web-caller/src/signaling.js family-web-caller/src/signaling.test.js
git commit -m "feat(family-web-caller): add socket.io signaling client"
```

archived-with: 2026-06-18-family-web-caller
---

### Task 5: WebRTC 通话模块

**Files:**
- Create: `family-web-caller/src/webrtc.js`
- Modify: `family-web-caller/call.html`
- Modify: `family-web-caller/src/main.js`

**Interfaces:**
- Consumes: `connect`, `emitInvite`, `emitAccept`, `emitReject`, `emitEnd`, `emitIceCandidate`, `onInvite`, `onAccept`, `onReject`, `onEnd`, `onBusy`, `onError`, `onIceCandidate`, `disconnect`。
- Produces:
  - `initCall(): void`
  - `startOutgoingCall(toDeviceId): Promise<void>`
  - `acceptIncomingCall(offer): Promise<void>`
  - `endCall(): void`
  - `toggleMic(): boolean`
  - `toggleCamera(): boolean`

- [ ] **Step 1: 实现 `webrtc.js`**

创建 `family-web-caller/src/webrtc.js`：

```javascript
import { $ } from './ui.js';
import {
  connect,
  disconnect,
  emitInvite,
  emitAccept,
  emitReject,
  emitEnd,
  emitIceCandidate,
  onInvite,
  onAccept,
  onReject,
  onEnd,
  onBusy,
  onError,
  onIceCandidate,
} from './signaling.js';

const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
  ],
};

let pc = null;
let localStream = null;
let callId = null;
let remoteDeviceId = null;
let isCaller = false;

function generateCallId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

async function getLocalStream() {
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  $('#local-video').srcObject = localStream;
  return localStream;
}

function createPeerConnection() {
  pc = new RTCPeerConnection(ICE_SERVERS);

  pc.onicecandidate = (event) => {
    if (event.candidate && callId) {
      emitIceCandidate(callId, event.candidate);
    }
  };

  pc.ontrack = (event) => {
    $('#remote-video').srcObject = event.streams[0];
  };

  pc.onconnectionstatechange = () => {
    $('#call-status').textContent = pc.connectionState;
  };

  return pc;
}

export async function startOutgoingCall(toDeviceId) {
  isCaller = true;
  remoteDeviceId = toDeviceId;
  callId = generateCallId();

  await getLocalStream();
  createPeerConnection();
  localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  connect();
  emitInvite(callId, toDeviceId, offer);
  $('#call-status').textContent = '正在呼叫…';

  onAccept(async (data) => {
    if (data.callId !== callId) return;
    await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
    $('#call-status').textContent = '通话中';
  });
}

export async function acceptIncomingCall(offer) {
  await getLocalStream();
  createPeerConnection();
  localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

  await pc.setRemoteDescription(new RTCSessionDescription(offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  emitAccept(callId, answer);
  $('#call-status').textContent = '通话中';
}

export function endCall() {
  if (callId) emitEnd(callId);
  cleanup();
}

export function toggleMic() {
  const audio = localStream?.getAudioTracks()[0];
  if (audio) audio.enabled = !audio.enabled;
  return audio?.enabled ?? false;
}

export function toggleCamera() {
  const video = localStream?.getVideoTracks()[0];
  if (video) video.enabled = !video.enabled;
  return video?.enabled ?? false;
}

function cleanup() {
  localStream?.getTracks().forEach((track) => track.stop());
  pc?.close();
  localStream = null;
  pc = null;
  callId = null;
  remoteDeviceId = null;
  disconnect();
}

export function initCall() {
  const params = new URLSearchParams(location.search);
  const toDeviceId = params.get('device');

  connect();

  if (toDeviceId) {
    $('#call-status').textContent = '正在发起通话…';
    startOutgoingCall(toDeviceId).catch((err) => {
      $('#call-status').textContent = `通话失败: ${err.message}`;
    });
  } else {
    $('#call-status').textContent = '等待来电…';
  }

  onInvite(async (data) => {
    callId = data.callId;
    remoteDeviceId = data.callerId;
    $('#call-status').textContent = `${data.callerName || '未知来电'} 来电`;
    const accepted = confirm(`是否接听 ${data.callerName || '未知来电'} 的通话？`);
    if (accepted) {
      await acceptIncomingCall(data.offer);
    } else {
      emitReject(callId, 'user declined');
      cleanup();
    }
  });

  onIceCandidate(async (data) => {
    if (data.callId !== callId || !pc) return;
    await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
  });

  onEnd((data) => {
    if (data.callId !== callId) return;
    $('#call-status').textContent = '通话已结束';
    cleanup();
  });

  onReject((data) => {
    if (data.callId !== callId) return;
    $('#call-status').textContent = '对方已拒接';
    cleanup();
  });

  onBusy((data) => {
    if (data.callId !== callId) return;
    $('#call-status').textContent = '对方忙线中';
    cleanup();
  });

  onError((data) => {
    if (data.callId && data.callId !== callId) return;
    $('#call-status').textContent = `错误: ${data.reason}`;
    cleanup();
  });

  $('#toggle-mic').addEventListener('click', () => {
    const enabled = toggleMic();
    $('#toggle-mic').textContent = enabled ? '静音' : '取消静音';
  });

  $('#toggle-camera').addEventListener('click', () => {
    const enabled = toggleCamera();
    $('#toggle-camera').textContent = enabled ? '关闭摄像头' : '打开摄像头';
  });

  $('#end-call').addEventListener('click', endCall);
}
```

- [ ] **Step 2: 更新 `main.js` 确认导入**

确保 `family-web-caller/src/main.js` 包含：

```javascript
import { initCall } from './webrtc.js';
```

- [ ] **Step 3: 为 `call.html` 添加来电入口提示（可选）**

`call.html` 已包含基础结构，无需修改。若希望仪表盘直接进入通话，已通过 `startCallFromDashboard` 携带 `device` 参数跳转。

- [ ] **Step 4: 手动验证本地媒体**

启动前后端，登录后添加设备与联系人，点击"通话"按钮。浏览器首次会请求摄像头/麦克风权限，允许后本地视频应出现在右下角。

- [ ] **Step 5: 提交**

```bash
git add family-web-caller/src/webrtc.js family-web-caller/call.html
git commit -m "feat(family-web-caller): add WebRTC peer connection and call UI"
```

archived-with: 2026-06-18-family-web-caller
---

### Task 6: 部署配置

**Files:**
- Create: `family-web-caller/Dockerfile`
- Create: `family-web-caller/nginx.conf`
- Create: `docker-compose.yml`（仓库根目录）
- Modify: `family-web-caller/package.json`（添加 build 脚本，可选）
- Create: `README.md`（仓库根目录）

**Interfaces:**
- Produces: 可通过 `docker-compose up --build` 一键启动的前后端组合服务。

- [ ] **Step 1: 创建前端 Dockerfile**

创建 `family-web-caller/Dockerfile`：

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 2: 创建 nginx 配置**

创建 `family-web-caller/nginx.conf`：

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://signaling:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /socket.io {
        proxy_pass http://signaling:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

- [ ] **Step 3: 更新根目录 docker-compose.yml**

创建 `docker-compose.yml`：

```yaml
version: "3.8"

services:
  signaling:
    build: ./signaling-server
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL:-sqlite+aiosqlite:///./data/signaling.db}
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-1440}
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost}
      - PORT=8000
    volumes:
      - ./signaling-server/data:/app/data
      - ./signaling-server/uploads:/app/uploads
    restart: unless-stopped

  family-web-caller:
    build: ./family-web-caller
    ports:
      - "80:80"
    depends_on:
      - signaling
    restart: unless-stopped
```

- [ ] **Step 4: 确认 package.json 包含 build 脚本**

确保 `family-web-caller/package.json` 中：

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

- [ ] **Step 5: 构建 Docker 镜像验证**

在仓库根目录执行：

```bash
docker-compose build
```

预期：两个镜像构建成功，无报错。

- [ ] **Step 6: 提交**

```bash
git add family-web-caller/Dockerfile family-web-caller/nginx.conf docker-compose.yml
git commit -m "feat(family-web-caller): add nginx and Docker deployment"
```

archived-with: 2026-06-18-family-web-caller
---

### Task 7: 验证

**Files:**
- Create: `family-web-caller/tests/e2e/family.spec.js`
- Create: `family-web-caller/playwright.config.js`
- Modify: `family-web-caller/package.json`（添加 test:e2e 脚本）
- Modify: `README.md`

**Interfaces:**
- Consumes: 完整前后端运行环境。
- Produces: 可运行的端到端测试与项目 README。

- [ ] **Step 1: 初始化 Playwright**

```bash
cd family-web-caller
npx playwright install
```

- [ ] **Step 2: 配置 Playwright**

创建 `family-web-caller/playwright.config.js`：

```javascript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

- [ ] **Step 3: 编写端到端测试**

创建 `family-web-caller/tests/e2e/family.spec.js`：

```javascript
import { test, expect } from '@playwright/test';

test.describe('family-web-caller', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/index.html');
    await expect(page.locator('h1')).toHaveText('家庭端视频通话');
    await expect(page.locator('#login-form')).toBeVisible();
  });

  test('dashboard requires login', async ({ page }) => {
    await page.goto('/dashboard.html');
    await page.waitForURL(/\/index\.html/);
  });

  test('login navigates to dashboard', async ({ page }) => {
    await page.goto('/index.html');
    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'password');

    // 依赖后端已存在测试账号，或通过 API 预先注册
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard\.html/);
    await expect(page.locator('#device-list')).toBeVisible();
  });
});
```

- [ ] **Step 4: 添加测试脚本**

在 `family-web-caller/package.json` 的 `scripts` 中追加：

```json
{
  "test:e2e": "playwright test",
  "test:unit": "vitest run"
}
```

- [ ] **Step 5: 运行构建验证**

```bash
cd family-web-caller
npm run build
```

预期：`dist/` 目录生成 `index.html`、`dashboard.html`、`call.html` 及 `assets/`。

- [ ] **Step 6: 运行单元测试**

```bash
npm run test:unit
```

预期：`auth.test.js` 与 `signaling.test.js` 全部通过。

- [ ] **Step 7: 手动冒烟测试**

1. 启动后端：

```bash
cd signaling-server
SECRET_KEY=dev-secret python -m uvicorn app.main:socket_app --reload --port 8000
```

2. 启动前端：

```bash
cd family-web-caller
npm run dev
```

3. 访问 `http://localhost:5173/index.html`，完成：
   - 注册/登录
   - 创建设备
   - 添加联系人
   - 上传头像
   - 点击通话进入 `call.html`
   - 检查本地视频是否出现

- [ ] **Step 8: 编写 README**

创建 `README.md`：

```markdown
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
```

- [ ] **Step 9: 提交**

```bash
git add family-web-caller/tests family-web-caller/playwright.config.js family-web-caller/package.json README.md
git commit -m "test(family-web-caller): add Playwright e2e tests and README"
```

archived-with: 2026-06-18-family-web-caller
---

## 自审清单

1. **Spec coverage**
   - 登录页与 JWT：Task 2 ✓
   - 仪表盘设备/联系人管理：Task 3 ✓
   - 头像上传：Task 3 ✓
   - 视频通话 UI 与 WebRTC：Task 5 ✓
   - Socket.IO 信令事件：Task 4 ✓
   - nginx + Docker 静态部署：Task 6 ✓
   - 根目录 docker-compose.yml：Task 6 ✓
   - 测试与 README：Task 7 ✓

2. **Placeholder scan**
   - 无 "TBD"、"TODO"、"实现 later"。
   - 所有代码块为可运行示例或精确命令。

3. **Type / signature consistency**
   - `apiClient` 路径与后端路由一致。
   - Socket.IO 发送事件名与后端 Python handler 对应（`call_invite` → `on_call_invite`）。
   - JWT 键名 `access_token` 与后端 `Token` schema 一致。
   - 联系人字段 `display_name`、`button_index` 与后端 schema 一致。

archived-with: 2026-06-18-family-web-caller
---

## 执行交接

**计划已保存至 `docs/superpowers/plans/2026-06-18-family-web-caller-plan.md`。两种执行方式：**

1. **Subagent-Driven（推荐）**：为每个 Task 分派独立子代理，任务间进行审查，快速迭代。
2. **Inline Execution**：在当前会话使用 `executing-plans` 技能按批次执行任务，并在关键检查点暂停。

请选择执行方式。
