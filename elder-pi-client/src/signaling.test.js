import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  connect,
  disconnect,
  onInvite,
  onAccept,
  onIceCandidate,
} from '../src/signaling.js';

const mockSocket = {
  connected: false,
  on: vi.fn(),
  emit: vi.fn(),
  disconnect: vi.fn(),
  removeAllListeners: vi.fn(),
};

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => mockSocket),
}));

describe('signaling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    disconnect();
    mockSocket.connected = false;
  });

  it('connects with device token', () => {
    const socket = connect();
    expect(socket).toBe(mockSocket);
    const authCall = mockSocket.on.mock.calls.find(([name]) => name === 'connect');
    expect(authCall).toBeDefined();
  });

  it('emits call:invite to handler', () => {
    const handler = vi.fn();
    onInvite(handler);
    connect();
    const [, inviteHandler] = mockSocket.on.mock.calls.find(([name]) => name === 'call:invite');
    inviteHandler({ callId: '1' });
    expect(handler).toHaveBeenCalledWith({ callId: '1' });
  });

  it('emits call:accept to handler', () => {
    const handler = vi.fn();
    onAccept(handler);
    connect();
    const [, acceptHandler] = mockSocket.on.mock.calls.find(([name]) => name === 'call:accept');
    acceptHandler({ callId: '2' });
    expect(handler).toHaveBeenCalledWith({ callId: '2' });
  });

  it('emits ice:candidate to handler', () => {
    const handler = vi.fn();
    onIceCandidate(handler);
    connect();
    const [, iceHandler] = mockSocket.on.mock.calls.find(([name]) => name === 'ice:candidate');
    iceHandler({ callId: '3' });
    expect(handler).toHaveBeenCalledWith({ callId: '3' });
  });
});
