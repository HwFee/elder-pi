import { $ } from './ui.js';
import {
  connect,
  disconnect,
  emitInvite,
  emitAccept,
  emitReject,
  emitEnd,
  emitIceCandidate,
  onInvite,
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
let isCaller = false;

function generateCallId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

async function getLocalStream() {
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  $('#local-video').srcObject = localStream;
  return localStream;
}

function createPeerConnection() {
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
    $('#call-status').textContent = pc.connectionState;
  };

  return pc;
}

export async function startOutgoingCall(toDeviceId) {
  isCaller = true;
  remoteDeviceId = toDeviceId;
  callId = generateCallId();

  await getLocalStream();
  createPeerConnection();
  localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  connect();
  emitInvite(callId, toDeviceId, offer);
  $('#call-status').textContent = '正在呼叫…';

  onAccept(async (data) => {
    if (data.callId !== callId) return;
    await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
    $('#call-status').textContent = '通话中';
  });
}

export async function acceptIncomingCall(offer) {
  await getLocalStream();
  createPeerConnection();
  localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

  await pc.setRemoteDescription(new RTCSessionDescription(offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  emitAccept(callId, answer);
  $('#call-status').textContent = '通话中';
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

function cleanup() {
  localStream?.getTracks().forEach((track) => track.stop());
  pc?.close();
  localStream = null;
  pc = null;
  callId = null;
  remoteDeviceId = null;
  disconnect();
}

export function initCall() {
  const params = new URLSearchParams(location.search);
  const toDeviceId = params.get('device');

  connect();

  if (toDeviceId) {
    $('#call-status').textContent = '正在发起通话…';
    startOutgoingCall(toDeviceId).catch((err) => {
      $('#call-status').textContent = `通话失败: ${err.message}`;
    });
  } else {
    $('#call-status').textContent = '等待来电…';
  }

  onInvite(async (data) => {
    callId = data.callId;
    remoteDeviceId = data.callerId;
    $('#call-status').textContent = `${data.callerName || '未知来电'} 来电`;
    const accepted = confirm(`是否接听 ${data.callerName || '未知来电'} 的通话？`);
    if (accepted) {
      await acceptIncomingCall(data.offer);
    } else {
      emitReject(callId, 'user declined');
      cleanup();
    }
  });

  onIceCandidate(async (data) => {
    if (data.callId !== callId || !pc) return;
    await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
  });

  onEnd((data) => {
    if (data.callId !== callId) return;
    $('#call-status').textContent = '通话已结束';
    cleanup();
  });

  onReject((data) => {
    if (data.callId !== callId) return;
    $('#call-status').textContent = '对方已拒接';
    cleanup();
  });

  onBusy((data) => {
    if (data.callId !== callId) return;
    $('#call-status').textContent = '对方忙线中';
    cleanup();
  });

  onError((data) => {
    if (data.callId && data.callId !== callId) return;
    $('#call-status').textContent = `错误: ${data.reason}`;
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
}
