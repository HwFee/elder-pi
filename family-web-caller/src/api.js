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
