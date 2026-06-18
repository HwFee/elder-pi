# contact-management Specification

## Purpose
TBD - created by archiving change video-call-signaling. Update Purpose after archive.
## Requirements
### Requirement: Create contact
The system SHALL allow an authenticated family member to create a contact for an elder device with a name, optional avatar, and optional button index.

#### Scenario: Successful contact creation
- **WHEN** an authenticated user posts valid contact data to `POST /api/devices/{deviceId}/contacts`
- **THEN** the system stores the contact and returns its id

### Requirement: List contacts
The system SHALL return all contacts for a given elder device.

#### Scenario: Device owner lists contacts
- **WHEN** the device owner requests `GET /api/devices/{deviceId}/contacts`
- **THEN** the system returns the contact list

#### Scenario: Unauthorized user lists contacts
- **WHEN** a user who does not own the device requests the contact list
- **THEN** the system returns a 403 error

### Requirement: Update contact
The system SHALL allow an authenticated owner to update a contact's name, avatar, or button index.

#### Scenario: Successful update
- **WHEN** the device owner sends a valid `PATCH /api/contacts/{contactId}`
- **THEN** the system updates the contact and returns the updated record

### Requirement: Delete contact
The system SHALL allow an authenticated owner to delete a contact.

#### Scenario: Successful deletion
- **WHEN** the device owner sends `DELETE /api/contacts/{contactId}`
- **THEN** the system removes the contact and returns 204

### Requirement: Button index uniqueness
The system SHALL ensure a button index is unique per elder device when assigned.

#### Scenario: Duplicate button index
- **WHEN** the owner creates a contact with a button index already used on the same device
- **THEN** the system returns a 409 error

