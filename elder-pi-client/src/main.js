import { getBackendUrl, getDeviceId, getDeviceToken } from './config.js';
import { $, show, hide, clearChildren, escapeHtml, setStatus } from './ui.js';
import { connect, disconnect, isConnected, onInvite, onEnd, onError } from './signaling.js';
import {
  startOutgoingCall,
  showIncomingCall,
  acceptIncomingCall,
  rejectIncomingCall,
  endCall,
  initCallHandlers,
} from './webrtc.js';

const screens = {
  home: $('#home-screen'),
  outgoing: $('#outgoing-screen'),
  incoming: $('#incoming-screen'),
  active: $('#active-screen'),
  setup: $('#setup-screen'),
};

let deviceId = getDeviceId();
let contacts = [];
let incomingTimeout = null;

function showScreen(name) {
  Object.values(screens).forEach((s) => hide(s));
  show(screens[name]);
}

async function apiClient(method, path, body = null) {
  const token = getDeviceToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers['Content-Type'] = 'application/json';

  const response = await fetch(`${getBackendUrl()}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`Request failed: ${response.status} ${text}`);
  }
  return response.status === 204 ? null : response.json();
}

function renderContacts() {
  const grid = $('#contacts-grid');
  clearChildren(grid);

  const sorted = [...contacts].sort((a, b) => a.button_index - b.button_index);
  for (const contact of sorted) {
    const btn = document.createElement('button');
    btn.className = 'contact-card';
    btn.dataset.device = contact.device_id;
    btn.dataset.user = contact.user_id;
    btn.dataset.name = contact.display_name;

    const img = document.createElement('img');
    img.alt = escapeHtml(contact.display_name);
    if (contact.avatar_path) {
      img.src = `${getBackendUrl()}/api/uploads/${contact.avatar_path}`;
    }

    const span = document.createElement('span');
    span.textContent = contact.display_name;

    btn.appendChild(img);
    btn.appendChild(span);
    btn.addEventListener('click', () => handleContactClick(contact));
    grid.appendChild(btn);
  }
}

async function handleContactClick(contact) {
  showScreen('outgoing');
  try {
    await startOutgoingCall(contact.device_id, contact.display_name);
    showScreen('active');
  } catch (err) {
    console.error(err);
    showScreen('home');
  }
}

function handleIncomingCall(data) {
  showIncomingCall(data);
  showScreen('incoming');

  incomingTimeout = window.setTimeout(() => {
    rejectIncomingCall();
    showScreen('home');
  }, 60000);
}

async function handleAnswer() {
  if (incomingTimeout) {
    window.clearTimeout(incomingTimeout);
    incomingTimeout = null;
  }
  try {
    await acceptIncomingCall();
    showScreen('active');
  } catch (err) {
    console.error(err);
    cleanupAndHome();
  }
}

function handleDecline() {
  if (incomingTimeout) {
    window.clearTimeout(incomingTimeout);
    incomingTimeout = null;
  }
  rejectIncomingCall();
  showScreen('home');
}

function cleanupAndHome() {
  endCall();
  showScreen('home');
}

async function bootstrap() {
  const token = getDeviceToken();
  if (!token) {
    showScreen('setup');
    return;
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    deviceId = payload.device_id || deviceId;
  } catch {
    // ignore parse errors
  }

  if (!deviceId) {
    $('#status-text').textContent = '无法识别设备 ID';
    return;
  }

  initCallHandlers();

  try {
    const data = await apiClient('GET', `/api/devices/${deviceId}/contacts`);
    contacts = data.contacts || [];
    renderContacts();
  } catch (err) {
    console.error('Failed to load contacts', err);
    $('#status-text').textContent = '加载联系人失败';
  }

  connect();

  onInvite((data) => {
    handleIncomingCall(data);
  });

  onEnd(() => {
    if (incomingTimeout) {
      window.clearTimeout(incomingTimeout);
      incomingTimeout = null;
    }
    cleanupAndHome();
  });

  onError((data) => {
    console.error('call error', data);
    cleanupAndHome();
  });

  $('#incoming-answer').addEventListener('click', () => handleAnswer());
  $('#incoming-decline').addEventListener('click', () => handleDecline());

  const socket = connect();
  socket.on('connect', () => setStatus(true));
  socket.on('disconnect', () => setStatus(false));
  setStatus(isConnected());
}

bootstrap();

window.addEventListener('beforeunload', () => {
  disconnect();
});
