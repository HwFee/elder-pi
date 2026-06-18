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
