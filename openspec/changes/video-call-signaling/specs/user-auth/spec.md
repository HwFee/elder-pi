## ADDED Requirements

### Requirement: User registration
The system SHALL allow a new family member to register with a unique email and a password.

#### Scenario: Successful registration
- **WHEN** a user submits a valid email and password to `POST /api/auth/register`
- **THEN** the system creates an account and returns the user id

#### Scenario: Duplicate email
- **WHEN** a user registers with an email that already exists
- **THEN** the system returns a 409 error

### Requirement: User login
The system SHALL authenticate a registered user and return an access token.

#### Scenario: Successful login
- **WHEN** a user submits correct email and password to `POST /api/auth/login`
- **THEN** the system returns a JWT access token

#### Scenario: Invalid credentials
- **WHEN** a user submits an incorrect password
- **THEN** the system returns a 401 error

### Requirement: Token validation
The system SHALL reject requests with missing or invalid tokens for protected endpoints.

#### Scenario: Valid token
- **WHEN** a request includes a valid access token in the `Authorization` header
- **THEN** the system allows access and identifies the caller

#### Scenario: Missing token
- **WHEN** a request omits the access token
- **THEN** the system returns a 401 error
