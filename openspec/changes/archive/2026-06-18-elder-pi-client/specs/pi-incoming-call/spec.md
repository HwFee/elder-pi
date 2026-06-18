## ADDED Requirements

### Requirement: Incoming call rings and shows caller info
The system SHALL display a full-screen incoming call UI with caller name and prominent answer/decline buttons when a `call:invite` event is received.

#### Scenario: Incoming call while idle
- **WHEN** a `call:invite` event arrives
- **THEN** the client SHALL play a ringing sound and show the caller's name and avatar
- **AND** the answer button SHALL be at least 150px in the shorter dimension

### Requirement: User can answer an incoming call
The system SHALL accept the call, create an answer, and emit `call_accept` when the answer button is activated.

#### Scenario: Answer call
- **WHEN** the user presses the answer button
- **THEN** the client SHALL stop the ringtone, set the remote description, create an answer, and emit `call_accept`
- **AND** the UI SHALL switch to the active call screen

### Requirement: User can decline an incoming call
The system SHALL emit `call_reject` and return to the home screen when the decline button is activated.

#### Scenario: Decline call
- **WHEN** the user presses the decline button
- **THEN** the client SHALL emit `call_reject` and return to the home screen

### Requirement: Missed call times out
The system SHALL automatically decline an incoming call if not answered within 60 seconds.

#### Scenario: No answer
- **WHEN** 60 seconds elapse without user action
- **THEN** the client SHALL emit `call_reject` with reason `timeout` and return to the home screen
