## ADDED Requirements

### Requirement: Login form
The system SHALL provide a login form that collects email and password.

#### Scenario: Successful login
- **WHEN** a family member enters valid credentials and submits
- **THEN** the system stores the JWT and redirects to the dashboard

#### Scenario: Invalid credentials
- **WHEN** a family member enters invalid credentials
- **THEN** the system displays an error message and stays on the login page

### Requirement: Token storage
The system SHALL store the JWT securely for subsequent authenticated requests.

#### Scenario: Token persists across reloads
- **WHEN** a logged-in user reloads the page
- **THEN** the token is still available and requests remain authenticated

#### Scenario: Token cleared on logout
- **WHEN** a user clicks logout
- **THEN** the token is removed and the user is redirected to login
