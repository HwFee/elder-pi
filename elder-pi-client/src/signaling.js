import { io } from 'socket.io-client';
import { getDeviceToken, getBackendUrl } from './config.js';

let socket = null;
const handlers = {
  invite: null,
  accept: null,
  reject: null,
  end: null,
  busy: null,
  error: null,
  iceCandidate: null,
};

export function connect() {
  if (socket?.connected) return socket;

  if (socket) {
    socket.disconnect();
    socket.removeAllListeners?.();
  }

  const backendUrl = getBackendUrl();
  const token = getDeviceToken();

  socket = io(`${backendUrl}/signaling`, {
    auth: { token },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 20,
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

  socket.on('call:invite', (data) => handlers.invite?.(data));
  socket.on('call:accept', (data) => handlers.accept?.(data));
  socket.on('call:reject', (data) => handlers.reject?.(data));
  socket.on('call:end', (data) => handlers.end?.(data));
  socket.on('call:busy', (data) => handlers.busy?.(data));
  socket.on('call:error', (data) => handlers.error?.(data));
  socket.on('ice:candidate', (data) => handlers.iceCandidate?.(data));

  return socket;
}

export function disconnect() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
  Object.keys(handlers).forEach((key) => {
    handlers[key] = null;
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
  handlers.invite = callback;
}

export function onAccept(callback) {
  handlers.accept = callback;
}

export function onReject(callback) {
  handlers.reject = callback;
}

export function onEnd(callback) {
  handlers.end = callback;
}

export function onBusy(callback) {
  handlers.busy = callback;
}

export function onError(callback) {
  handlers.error = callback;
}

export function onIceCandidate(callback) {
  handlers.iceCandidate = callback;
}

export function isConnected() {
  return socket?.connected ?? false;
}
