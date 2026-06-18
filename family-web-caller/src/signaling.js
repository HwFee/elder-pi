import { io } from 'socket.io-client';
import { getToken } from './auth.js';

let socket = null;
const handlers = {
  invite: [],
  accept: [],
  reject: [],
  end: [],
  busy: [],
  error: [],
  iceCandidate: [],
};

export function connect() {
  if (socket?.connected) return socket;

  socket = io('/signaling', {
    auth: { token: getToken() },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 10,
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

  socket.on('call:invite', (data) => handlers.invite.forEach((cb) => cb(data)));
  socket.on('call:accept', (data) => handlers.accept.forEach((cb) => cb(data)));
  socket.on('call:reject', (data) => handlers.reject.forEach((cb) => cb(data)));
  socket.on('call:end', (data) => handlers.end.forEach((cb) => cb(data)));
  socket.on('call:busy', (data) => handlers.busy.forEach((cb) => cb(data)));
  socket.on('call:error', (data) => handlers.error.forEach((cb) => cb(data)));
  socket.on('ice:candidate', (data) => handlers.iceCandidate.forEach((cb) => cb(data)));

  return socket;
}

export function disconnect() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
  Object.keys(handlers).forEach((key) => {
    handlers[key] = [];
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
  handlers.invite.push(callback);
}

export function onAccept(callback) {
  handlers.accept.push(callback);
}

export function onReject(callback) {
  handlers.reject.push(callback);
}

export function onEnd(callback) {
  handlers.end.push(callback);
}

export function onBusy(callback) {
  handlers.busy.push(callback);
}

export function onError(callback) {
  handlers.error.push(callback);
}

export function onIceCandidate(callback) {
  handlers.iceCandidate.push(callback);
}
