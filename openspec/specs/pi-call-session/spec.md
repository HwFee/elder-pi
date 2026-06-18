# pi-call-session Specification

## Purpose
TBD - created by archiving change elder-pi-client. Update Purpose after archive.
## Requirements
### Requirement: Local and remote video are displayed during a call
The system SHALL show the local video in a small overlay and the remote video full-screen while a call is active.

#### Scenario: Active call
- **WHEN** a call is accepted or the remote party accepts
- **THEN** the remote video stream SHALL be rendered full-screen
- **AND** the local video stream SHALL be visible in a corner overlay

### Requirement: Call can be muted
The system SHALL toggle the microphone on/off when a mute button is pressed and update the button label.

#### Scenario: Mute and unmute
- **WHEN** the user presses the mute button
- **THEN** the local audio track SHALL be disabled
- **WHEN** the user presses the button again
- **THEN** the local audio track SHALL be re-enabled

### Requirement: Camera can be disabled
The system SHALL toggle the local camera on/off when a camera button is pressed.

#### Scenario: Disable and enable camera
- **WHEN** the user presses the camera-off button
- **THEN** the local video track SHALL be disabled
- **WHEN** the user presses the button again
- **THEN** the local video track SHALL be re-enabled

### Requirement: Call can be ended
The system SHALL emit `call_end`, stop media tracks, close the peer connection, and return to the home screen when the end-call button is pressed.

#### Scenario: End call
- **WHEN** the user presses the end-call button
- **THEN** the client SHALL emit `call_end`
- **AND** media tracks SHALL stop
- **AND** the peer connection SHALL close
- **AND** the UI SHALL return to the home screen

### Requirement: Remote hang-up returns to home
The system SHALL return to the home screen when a `call:end` event is received.

#### Scenario: Remote ends call
- **WHEN** a `call:end` event is received
- **THEN** the client SHALL clean up the peer connection and media
- **AND** the UI SHALL return to the home screen

