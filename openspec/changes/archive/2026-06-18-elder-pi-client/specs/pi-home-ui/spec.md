## ADDED Requirements

### Requirement: Contacts are rendered as large buttons
The system SHALL display contacts for the device as large, tappable buttons ordered by `button_index`.

#### Scenario: Contacts loaded
- **WHEN** the client receives the contact list from `/api/devices/:id/contacts`
- **THEN** each contact SHALL be shown as a button with avatar and display name occupying at least 120px in the shorter dimension

### Requirement: Tapping a contact initiates a call
The system SHALL emit a `call_invite` event to the contact's associated user when a contact button is tapped.

#### Scenario: Outgoing call from home
- **WHEN** the user taps a contact button
- **THEN** the client SHALL create a WebRTC offer and emit `call_invite` with the contact's `user_id`
- **AND** the UI SHALL switch to the outgoing call screen

### Requirement: Home screen shows device status
The system SHALL indicate whether the device is online and ready to receive calls.

#### Scenario: Online state
- **WHEN** the socket is connected
- **THEN** a visual ready indicator SHALL be visible

#### Scenario: Offline state
- **WHEN** the socket is disconnected
- **THEN** an offline message SHALL replace or overlay the home screen
