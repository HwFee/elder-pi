from datetime import datetime, timedelta
from typing import Optional


class ConnectionManager:
    def __init__(self):
        self._sid_to_device: dict[str, str] = {}
        self._device_to_sids: dict[str, set[str]] = {}
        self._last_seen: dict[str, datetime] = {}

    def connect(self, sid: str, device_id: str):
        self._sid_to_device[sid] = device_id
        self._device_to_sids.setdefault(device_id, set()).add(sid)
        self._last_seen[device_id] = datetime.utcnow()

    def disconnect(self, sid: str):
        device_id = self._sid_to_device.pop(sid, None)
        if device_id:
            sids = self._device_to_sids.get(device_id, set())
            sids.discard(sid)
            if not sids:
                self._device_to_sids.pop(device_id, None)

    def is_online(self, device_id: str) -> bool:
        return device_id in self._device_to_sids and len(self._device_to_sids[device_id]) > 0

    def get_last_seen(self, device_id: str) -> Optional[datetime]:
        return self._last_seen.get(device_id)

    def heartbeat(self, device_id: str, sid: Optional[str] = None):
        self._last_seen[device_id] = datetime.utcnow()
        if sid is not None:
            self._sid_to_device[sid] = device_id
            self._device_to_sids.setdefault(device_id, set()).add(sid)

    def get_room_for_device(self, device_id: str) -> str:
        return f"device:{device_id}"

    def sweep_stale(self, timeout_seconds: int = 60):
        cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        stale = [device_id for device_id, last_seen in self._last_seen.items() if last_seen < cutoff]
        for device_id in stale:
            sids = self._device_to_sids.pop(device_id, set())
            for sid in sids:
                self._sid_to_device.pop(sid, None)
        for device_id in stale:
            self._last_seen.pop(device_id, None)
        return stale


manager = ConnectionManager()
