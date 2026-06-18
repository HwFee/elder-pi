## Verification Report: video-call-signaling

### Summary
| Dimension    | Status |
|--------------|--------|
| Completeness | 44/44 tasks, 18/18 requirements |
| Correctness  | 43/43 tests passed; all core flows exercised |
| Coherence    | Followed design; minor status-code/field divergences noted |

### Test Results
```bash
cd signaling-server
$env:SECRET_KEY='test-secret'
python -m pytest tests/ -v
```

Result: **43 passed in 31.47s**.

Key coverage includes:
- User registration/login and password/token helpers (`tests/test_auth.py`, `tests/test_auth_service.py`)
- Device creation/retrieval and status (`tests/test_devices.py`, `tests/test_presence.py`)
- Contact CRUD and button-index uniqueness (`tests/test_contacts.py`)
- Avatar upload validation and static serving (`tests/test_uploads.py`)
- Socket.IO auth, heartbeat, call lifecycle, ICE relay, busy guard, and unauthorized rejection (`tests/test_signaling.py`, `tests/test_whitelist.py`)
- End-to-end call smoke flow (`tests/test_smoke.py`)

### Requirement/Implementation Mapping

**user-auth (3 requirements)**
- Registration / login / token validation implemented in `app/routers/auth.py:15-43` and `app/dependencies.py:14-28`.
- Password hashing & JWT helpers in `app/services/auth_service.py:12-33`.

**contact-management (5 requirements)**
- CRUD, ownership checks, and button-index uniqueness in `app/routers/contacts.py:14-94` and `app/services/contact_service.py:15-110`.
- Avatar upload in `app/routers/contacts.py:77-94` and `app/services/upload_service.py:30-45`.

**whitelist (2 requirements)**
- Caller authorization check in `app/socket/namespace.py:98-105`.
- `call:error` emission for unauthorized callers in `app/socket/namespace.py:100-104`.

**call-signaling (6 requirements)**
- `call:invite` validation/forwarding in `app/socket/namespace.py:65-132`.
- `call:accept` / `call:reject` / `call:end` forwarding in `app/socket/namespace.py:134-199`.
- `ice:candidate` relay in `app/socket/namespace.py:201-224`.
- Single-active-call guard in `app/socket/namespace.py:107-121` and DB-level partial unique index in `app/models.py:70-77`.
- Call session lifecycle persistence in `app/services/call_service.py:10-71`.

**presence (2 requirements)**
- Heartbeat handler in `app/socket/namespace.py:59-63` and `ConnectionManager` in `app/socket/manager.py:5-51`.
- Status endpoint in `app/routers/devices.py:45-59`.

### Issues by Priority

#### CRITICAL
None

#### WARNING
1. **Duplicate email registration returns 400 instead of 409.**  
   `specs/user-auth/spec.md` requires a 409 for duplicate email; `app/routers/auth.py:19` returns 400.  
   Recommendation: Change `status_code` to `409` or map the existing email check to `409`.

2. **Duplicate button index on contact creation returns 400 instead of 409.**  
   `specs/contact-management/spec.md` requires a 409 for duplicate button index; `app/routers/contacts.py:27` returns 400.  
   Recommendation: Return `status.HTTP_409_CONFLICT` when `contact_service.create_contact` reports a duplicate button index.

3. **Unauthorized contact list request returns 404 instead of 403.**  
   `specs/contact-management/spec.md` requires a 403 when a non-owner lists contacts; `app/routers/contacts.py:40` maps the ownership failure to 404.  
   Recommendation: Distinguish "device not found" from "not owner" in `contact_service.list_contacts` and return 403 for the latter.

4. **Device model omits `last_seen_at` field specified in design.**  
   `design.md` Decision 4 lists `Device.lastSeenAt`; `app/models.py:27-39` has no such column. Presence state is tracked only in-memory in `ConnectionManager`.  
   Recommendation: Add `last_seen_at` to `Device` and update it on heartbeat, or revise `design.md` to reflect the in-memory-only approach.

#### SUGGESTION
1. **Add explicit test for contact-deletion revoking whitelist permission.**  
   The scenario in `specs/whitelist/spec.md` is implemented (`app/services/contact_service.py:94-103`) but not directly tested.  
   Recommendation: Extend `tests/test_whitelist.py` to delete a contact and assert the next `call:invite` is rejected.

2. **Add DB-state assertion for rejected calls.**  
   `tests/test_signaling.py::test_call_reject_forwarded_to_caller` verifies the forwarded event but not the persisted `status`.  
   Recommendation: Assert `CallSession.status == "rejected"` and `ended_at is not None` after rejection.

3. **Remove unused import.**  
   `app/models.py:5` imports `PG_UUID` but never uses it.  
   Recommendation: Delete the unused import.

4. **Standardize ownership/auth failure status codes.**  
   Several routes return 404 for ownership failures (`app/routers/devices.py:40-42`, `app/routers/contacts.py:58-62, 72-74`). While acceptable internally, consider returning 403 where the resource exists but access is denied, to align with the contact-list spec scenario.

### Final Assessment
No critical issues. Four warnings are behavioral/spec divergences that should be addressed before considering the implementation fully spec-compliant, but none block runtime operation. The full test suite passes and all major capabilities are implemented and covered.

**Ready for archive (with noted improvements).**
