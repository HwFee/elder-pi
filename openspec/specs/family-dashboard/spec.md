# family-dashboard Specification

## Purpose
TBD - created by archiving change family-web-caller. Update Purpose after archive.
## Requirements
### Requirement: Device list
The system SHALL display a list of elder devices owned by the logged-in user.

#### Scenario: Device online
- **WHEN** the dashboard loads
- **THEN** each device shows its display name and online status

### Requirement: Contact list
The system SHALL display contacts for a selected device.

#### Scenario: View contacts
- **WHEN** a user selects a device
- **THEN** the system shows contacts with avatar, name, and button index

### Requirement: Create contact
The system SHALL allow the user to add a new contact for a device.

#### Scenario: Add contact
- **WHEN** a user fills in name, selects button index, and saves
- **THEN** the contact appears in the list

### Requirement: Update contact
The system SHALL allow the user to edit a contact's name, button index, or avatar.

#### Scenario: Edit contact
- **WHEN** a user changes contact information and saves
- **THEN** the contact is updated in the list

### Requirement: Delete contact
The system SHALL allow the user to remove a contact.

#### Scenario: Remove contact
- **WHEN** a user confirms deletion of a contact
- **THEN** the contact disappears from the list and the caller loses permission

### Requirement: Avatar upload
The system SHALL allow uploading an avatar image for a contact.

#### Scenario: Upload avatar
- **WHEN** a user selects an image file and saves
- **THEN** the avatar is displayed for that contact

