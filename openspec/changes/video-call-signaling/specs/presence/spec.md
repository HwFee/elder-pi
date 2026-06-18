## ADDED Requirements

### Requirement: Heartbeat
The system SHALL receive periodic heartbeats from an elder device to track liveness.

#### Scenario: Elder device sends heartbeat
- **WHEN** the elder device emits `presence:heartbeat` over its authenticated WebSocket connection
- **THEN** the system updates the device's `lastSeenAt` timestamp

### Requirement: Query device online status
The system SHALL allow an authenticated family member to query whether an elder device is currently online.

#### Scenario: Online device
- **WHEN** an authenticated user requests `GET /api/devices/{deviceId}/status`
- **THEN** the system returns `online: true` if the device has sent a heartbeat within the configured timeout window

#### Scenario: Offline device
- **WHEN** an authenticated user requests status for a device that has not sent a heartbeat within the timeout window
- **THEN** the system returns `online: false`
