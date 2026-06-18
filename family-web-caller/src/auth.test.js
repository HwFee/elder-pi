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
