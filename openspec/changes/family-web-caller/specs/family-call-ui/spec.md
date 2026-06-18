## ADDED Requirements

### Requirement: Initiate call
The system SHALL allow a family member to initiate a video call to an elder device.

#### Scenario: Start call
- **WHEN** a user clicks the call button on a contact
- **THEN** the system creates a WebRTC offer, sends `call:invite`, and shows the call UI

#### Scenario: Callee accepts
- **WHEN** the elder device emits `call:accept`
- **THEN** the system sets the remote description and displays the remote video

#### Scenario: Callee rejects
- **WHEN** the elder device emits `call:reject`
- **THEN** the system shows a rejected message and closes the call UI

#### Scenario: Callee busy
- **WHEN** the server emits `call:busy`
- **THEN** the system shows a busy message and closes the call UI

### Requirement: Receive call
The system SHALL display an incoming call screen when the server forwards a `call:invite`.

#### Scenario: Incoming call
- **WHEN** the server emits `call:invite` for the logged-in user
- **THEN** the system plays a ringtone, shows the caller name, and provides accept/reject buttons

#### Scenario: Accept incoming call
- **WHEN** a user clicks accept
- **THEN** the system creates an answer, emits `call:accept`, and opens the call UI

### Requirement: End call
The system SHALL allow either side to end the active call.

#### Scenario: User ends call
- **WHEN** a user clicks the hang-up button
- **THEN** the system emits `call:end` and closes the call UI

#### Scenario: Remote ends call
- **WHEN** the server emits `call:end`
- **THEN** the system closes the call UI

### Requirement: ICE relay
The system SHALL send and receive ICE candidates during a call.

#### Scenario: Send ICE candidate
- **WHEN** the local peer connection gathers a candidate
- **THEN** the system emits `ice:candidate` to the server

#### Scenario: Receive ICE candidate
- **WHEN** the server emits `ice:candidate`
- **THEN** the system adds the candidate to the peer connection

### Requirement: Media controls
The system SHALL provide mute and camera-off toggles during a call.

#### Scenario: Mute audio
- **WHEN** a user clicks the mute button
- **THEN** the local audio track is disabled

#### Scenario: Disable camera
- **WHEN** a user clicks the camera-off button
- **THEN** the local video track is disabled and the remote side sees a placeholder
