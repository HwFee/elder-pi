## ADDED Requirements

### Requirement: Device token is loaded at startup
The system SHALL read a persisted device token from `~/.config/elder-pi/device-token` on launch.

#### Scenario: Token file exists
- **WHEN** the client starts and the token file is present
- **THEN** the client SHALL read the token and attempt to connect to the signaling server

#### Scenario: Token file missing
- **WHEN** the client starts and no token file exists
- **THEN** the client SHALL display a setup screen with instructions for pairing

### Requirement: Client starts automatically on boot
The system SHALL provide a systemd user service or init script that starts the client automatically after the graphical session is available.

#### Scenario: Reboot device
- **WHEN** the Raspberry Pi boots
- **THEN** the client SHALL start without manual login within 60 seconds

### Requirement: Client reconnects on network loss
The system SHALL automatically reconnect to the signaling server when the network becomes available again.

#### Scenario: WiFi drops and returns
- **WHEN** the network connection drops
- **THEN** the client SHALL show an offline indicator
- **WHEN** the network returns
- **THEN** the client SHALL reconnect and clear the offline indicator
