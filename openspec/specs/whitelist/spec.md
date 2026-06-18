# whitelist Specification

## Purpose
TBD - created by archiving change video-call-signaling. Update Purpose after archive.
## Requirements
### Requirement: Whitelist-based call permission
The system SHALL only forward a call invitation if the caller is a contact of the target elder device.

#### Scenario: Authorized caller
- **WHEN** an authenticated caller who is in the target device's contact list emits `call:invite`
- **THEN** the system forwards the invitation to the elder device

#### Scenario: Unauthorized caller
- **WHEN** an authenticated caller who is not in the target device's contact list emits `call:invite`
- **THEN** the system emits `call:error` to the caller with a forbidden reason and does not forward the invitation

### Requirement: Contact deletion revokes permission
The system SHALL treat a deleted contact as no longer authorized to call the device.

#### Scenario: Former caller is removed
- **WHEN** a previously authorized contact is deleted from the device
- **THEN** any subsequent `call:invite` from that user is rejected

