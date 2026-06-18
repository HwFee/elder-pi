# call-signaling Specification

## Purpose
TBD - created by archiving change video-call-signaling. Update Purpose after archive.
## Requirements
### Requirement: Invite a device to a call
The system SHALL forward a call invitation from an authenticated caller to the target elder device over WebSocket.

#### Scenario: Caller invites elder device
- **WHEN** an authenticated caller emits `call:invite` with a valid target device id and WebRTC offer
- **THEN** the system validates the caller is whitelisted and forwards the invitation to the elder device

### Requirement: Accept a call
The system SHALL forward an accept event from the elder device back to the caller.

#### Scenario: Elder device accepts
- **WHEN** the elder device emits `call:accept` with the call id and WebRTC answer
- **THEN** the system forwards the event to the original caller

### Requirement: Reject a call
The system SHALL forward a reject event from the elder device to the caller.

#### Scenario: Elder device rejects
- **WHEN** the elder device emits `call:reject` with the call id
- **THEN** the system forwards the event to the caller and closes the call session

### Requirement: End a call
The system SHALL forward an end event from either side to the other side and record the call as ended.

#### Scenario: Caller ends call
- **WHEN** the caller emits `call:end` with the call id
- **THEN** the system forwards the event to the elder device and updates the call session status to ended

### Requirement: Relay ICE candidates
The system SHALL relay ICE candidates between caller and elder device during a call.

#### Scenario: Caller sends ICE candidate
- **WHEN** the caller emits `ice:candidate` with the call id and candidate payload
- **THEN** the system forwards the candidate to the elder device

### Requirement: Single active call per device
The system SHALL reject a new invitation if the elder device already has an active call.

#### Scenario: Device busy
- **WHEN** a caller invites a device that already has an active call
- **THEN** the system returns `call:busy` to the caller

