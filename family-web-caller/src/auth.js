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

export function initLogin() {
  const form = document.getElementById('login-form');
  const errorEl = document.getElementById('login-error');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (errorEl) errorEl.textContent = '';

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
      await login(email, password);
      window.location.href = '/dashboard.html';
    } catch (err) {
      if (errorEl) errorEl.textContent = err.message;
    }
  });
}
