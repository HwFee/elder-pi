import { describe, it, expect, beforeEach } from 'vitest';
import { getDeviceToken, setDeviceToken, getBackendUrl, getDeviceId } from '../src/config.js';

describe('config', () => {
  beforeEach(() => {
    localStorage.clear();
    delete window.__ELDER_PI_CONFIG__;
  });

  it('reads token from localStorage', () => {
    setDeviceToken('token-1');
    expect(getDeviceToken()).toBe('token-1');
  });

  it('prefers injected config over localStorage', () => {
    setDeviceToken('token-1');
    window.__ELDER_PI_CONFIG__ = { deviceToken: 'token-2' };
    expect(getDeviceToken()).toBe('token-2');
  });

  it('returns default backend url', () => {
    expect(getBackendUrl()).toBe('http://127.0.0.1:8000');
  });

  it('reads injected backend url', () => {
    window.__ELDER_PI_CONFIG__ = { backendUrl: 'http://pi.local:8000' };
    expect(getBackendUrl()).toBe('http://pi.local:8000');
  });

  it('returns null device id by default', () => {
    expect(getDeviceId()).toBeNull();
  });
});
