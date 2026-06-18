import { getToken, logout } from './auth.js';
import { $, clearChildren, escapeHtml, show, hide } from './ui.js';

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
