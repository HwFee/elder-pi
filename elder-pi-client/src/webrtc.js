import { $ } from './ui.js';
import {
  connect,
  disconnect,
  emitInvite,
  emitAccept,
  emitReject,
  emitEnd,
  emitIceCandidate,
  onAccept,
  onReject,
  onEnd,
  onBusy,
  onError,
  onIceCandidate,
} from './signaling.js';

const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
  ],
};

let pc = null;
let localStream = null;
let callId = null;
let remoteDeviceId = null;
let incomingOffer = null;

function generateCallId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

async function getLocalStream() {
  if (localStream) {
    localStream.getTracks().forEach((track) => track.stop());
    localStream = null;
  }
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  $('#local-video').srcObject = localStream;
  return localStream;
}

function createPeerConnection() {
  if (pc) {
    pc.onicecandidate = null;
    pc.ontrack = null;
    pc.onconnectionstatechange = null;
    pc.close();
    pc = null;
  }

  pc = new RTCPeerConnection(ICE_SERVERS);

  pc.onicecandidate = (event) => {
    if (event.candidate && callId) {
      emitIceCandidate(callId, event.candidate);
    }
  };

  pc.ontrack = (event) => {
    $('#remote-video').srcObject = event.streams[0];
  };

  pc.onconnectionstatechange = () => {
    console.info('peer connection state', pc.connectionState);
  };

  return pc;
}

function cleanup() {
  localStream?.getTracks().forEach((track) => track.stop());
  if (pc) {
    pc.onicecandidate = null;
    pc.ontrack = null;
    pc.onconnectionstatechange = null;
    pc.close();
  }
  localStream = null;
  pc = null;
  callId = null;
  remoteDeviceId = null;
  incomingOffer = null;
  $('#remote-video').srcObject = null;
  $('#local-video').srcObject = null;
}

export async function startOutgoingCall(toDeviceId, displayName) {
  remoteDeviceId = toDeviceId;
  callId = generateCallId();

  await getLocalStream();
  createPeerConnection();
  localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  connect();
  emitInvite(callId, toDeviceId, offer);

  $('#outgoing-name').textContent = `正在呼叫 ${displayName || ''}…`.trim();

  onAccept(async (data) => {
    if (data.callId !== callId) return;
    await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
  });

  onReject((data) => {
    if (data.callId !== callId) return;
    endCall();
  });

  onBusy((data) => {
    if (data.callId !== callId) return;
    endCall();
  });

  onError((data) => {
    if (data.callId && data.callId !== callId) return;
    endCall();
  });
}

export function showIncomingCall(data) {
  callId = data.callId;
  remoteDeviceId = data.callerId;
  incomingOffer = data.offer;

  $('#incoming-name').textContent = data.callerName || '未知来电';
  const avatar = $('#incoming-avatar');
  if (data.callerAvatar) {
    avatar.src = data.callerAvatar;
    avatar.hidden = false;
  } else {
    avatar.hidden = true;
  }
}

export async function acceptIncomingCall() {
  if (!incomingOffer) return;
  await getLocalStream();
  createPeerConnection();
  localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

  await pc.setRemoteDescription(new RTCSessionDescription(incomingOffer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  emitAccept(callId, answer);
}

export function rejectIncomingCall() {
  emitReject(callId, 'user declined');
  cleanup();
}

export function endCall() {
  if (callId) emitEnd(callId);
  cleanup();
}

export function toggleMic() {
  const audio = localStream?.getAudioTracks()[0];
  if (audio) audio.enabled = !audio.enabled;
  return audio?.enabled ?? false;
}

export function toggleCamera() {
  const video = localStream?.getVideoTracks()[0];
  if (video) video.enabled = !video.enabled;
  return video?.enabled ?? false;
}

export function initCallHandlers() {
  onIceCandidate(async (data) => {
    if (data.callId !== callId || !pc) return;
    await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
  });

  onEnd((data) => {
    if (data.callId !== callId) return;
    cleanup();
  });

  $('#toggle-mic').addEventListener('click', () => {
    const enabled = toggleMic();
    $('#toggle-mic').textContent = enabled ? '静音' : '取消静音';
  });

  $('#toggle-camera').addEventListener('click', () => {
    const enabled = toggleCamera();
    $('#toggle-camera').textContent = enabled ? '关闭摄像头' : '打开摄像头';
  });

  $('#end-call').addEventListener('click', endCall);
  $('#outgoing-cancel').addEventListener('click', endCall);
  $('#incoming-answer').addEventListener('click', () => acceptIncomingCall().catch(() => cleanup()));
  $('#incoming-decline').addEventListener('click', rejectIncomingCall);
}
