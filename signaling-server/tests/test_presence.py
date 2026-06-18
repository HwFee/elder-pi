from datetime import datetime, timedelta

import pytest
import time
from app.socket.manager import ConnectionManager


def test_manager_tracks_online_status():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    assert mgr.is_online("device-1") is True
    mgr.disconnect("sid-1")
    assert mgr.is_online("device-1") is False


def test_heartbeat_updates_last_seen():
    mgr = ConnectionManager()
    mgr.connect("sid-1", "device-1")
    old = mgr.get_last_seen("device-1")
    time.sleep(0.01)
    mgr.heartbeat("device-1")
    new = mgr.get_last_seen("device-1")
    assert new > old
