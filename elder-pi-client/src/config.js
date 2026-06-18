const TOKEN_KEY = 'elder_pi_device_token';

export function getDeviceToken() {
  if (window.__ELDER_PI_CONFIG__?.deviceToken) {
    return window.__ELDER_PI_CONFIG__.deviceToken;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function setDeviceToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getBackendUrl() {
  return window.__ELDER_PI_CONFIG__?.backendUrl || 'http://127.0.0.1:8000';
}

export function getDeviceId() {
  return window.__ELDER_PI_CONFIG__?.deviceId || null;
}
