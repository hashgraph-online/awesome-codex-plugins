# EARS Notation Reference

EARS (Easy Approach to Requirements Syntax) provides a structured format for writing clear, testable requirements.

## Core Pattern

```
WHEN [precondition/trigger]
THE SYSTEM SHALL [expected behavior]
```

## Pattern Variations

### Ubiquitous Requirements

For behavior that should always occur:

```
THE SYSTEM SHALL [behavior]
```

**Example:**
```
THE SYSTEM SHALL encrypt all data at rest using AES-256
THE SYSTEM SHALL log all authentication attempts
```

### Event-Driven Requirements

For behavior triggered by specific events:

```
WHEN [event occurs]
THE SYSTEM SHALL [response]
```

**Example:**
```
WHEN a user clicks the submit button
THE SYSTEM SHALL validate all form fields before submission

WHEN a payment is processed successfully
THE SYSTEM SHALL send a confirmation email to the user
```

### State-Driven Requirements

For behavior dependent on system state:

```
WHILE [state condition]
THE SYSTEM SHALL [behavior]
```

**Example:**
```
WHILE the user is logged in
THE SYSTEM SHALL display the user's profile in the navigation bar

WHILE the system is in maintenance mode
THE SYSTEM SHALL display a maintenance notification banner
```

### Conditional Requirements

For behavior with conditions:

```
IF [condition]
WHEN [trigger]
THE SYSTEM SHALL [behavior]
```

**Example:**
```
IF the user has admin privileges
WHEN they access the settings page
THE SYSTEM SHALL display advanced configuration options

IF the cart total exceeds $100
WHEN the user proceeds to checkout
THE SYSTEM SHALL apply free shipping
```

### Negative Requirements

For behavior that must NOT occur:

```
THE SYSTEM SHALL NOT [prohibited behavior]
```

**Example:**
```
THE SYSTEM SHALL NOT store passwords in plain text
THE SYSTEM SHALL NOT allow more than 5 failed login attempts per hour
```

### Optional Features

For features that may or may not be implemented:

```
THE SYSTEM MAY [optional behavior]
```

**Example:**
```
THE SYSTEM MAY suggest related products based on browsing history
THE SYSTEM MAY cache API responses for improved performance
```

## Complete Examples by Domain

### Authentication

```
US-1: User Login

WHEN a user submits valid credentials
THE SYSTEM SHALL authenticate the user and create a session

WHEN a user submits invalid credentials
THE SYSTEM SHALL display an error message without revealing which field is incorrect

WHEN a user fails authentication 5 times within 15 minutes
THE SYSTEM SHALL temporarily lock the account for 30 minutes

WHEN a user requests password reset
THE SYSTEM SHALL send a reset link valid for 1 hour

THE SYSTEM SHALL NOT store passwords in plain text
THE SYSTEM SHALL hash passwords using bcrypt with cost factor 12
```

### Form Validation

```
US-2: Form Validation

WHEN a user submits a form with missing required fields
THE SYSTEM SHALL highlight the missing fields and display inline error messages

WHEN a user enters an invalid email format
THE SYSTEM SHALL display "Please enter a valid email address"

WHEN a user enters a password shorter than 8 characters
THE SYSTEM SHALL display password strength requirements

WHILE the user is typing in a field with validation errors
THE SYSTEM SHALL clear the error when the input becomes valid
```

### API Interactions

```
US-3: API Error Handling

WHEN an API request times out after 30 seconds
THE SYSTEM SHALL retry the request up to 3 times with exponential backoff

WHEN an API returns a 4xx error
THE SYSTEM SHALL display a user-friendly error message

WHEN an API returns a 5xx error
THE SYSTEM SHALL display "Service temporarily unavailable" and log the error

IF the user is offline
WHEN they attempt an API request
THE SYSTEM SHALL queue the request and retry when connectivity is restored
```

### Data Management

```
US-4: Data CRUD Operations

WHEN a user creates a new record
THE SYSTEM SHALL validate all required fields before saving

WHEN a user updates a record
THE SYSTEM SHALL maintain an audit trail of changes

WHEN a user deletes a record
THE SYSTEM SHALL soft-delete by setting a deleted_at timestamp

WHEN a user requests deleted records
THE SYSTEM SHALL NOT include soft-deleted records unless explicitly requested
```

### Real-time Features

```
US-5: Live Updates

WHILE a user is viewing a dashboard
THE SYSTEM SHALL refresh data every 30 seconds

WHEN new data is available
THE SYSTEM SHALL display a notification without refreshing the page

WHEN the WebSocket connection is lost
THE SYSTEM SHALL attempt to reconnect with exponential backoff

WHEN reconnection fails after 5 attempts
THE SYSTEM SHALL fall back to polling every 60 seconds
```

## Writing Tips

### Be Specific

**Vague:**
```
WHEN the user makes an error
THE SYSTEM SHALL handle it gracefully
```

**Specific:**
```
WHEN the user submits a form with invalid data
THE SYSTEM SHALL display inline validation errors next to each invalid field
```

### Include Measurable Criteria

**Unmeasurable:**
```
THE SYSTEM SHALL respond quickly
```

**Measurable:**
```
THE SYSTEM SHALL respond to API requests within 200ms for the 95th percentile
```

### Cover Edge Cases

Consider:
- Empty states
- Error conditions
- Boundary values
- Concurrent operations
- Offline/degraded states

### One Behavior Per Requirement

**Bundled (avoid):**
```
WHEN a user logs in
THE SYSTEM SHALL authenticate them, create a session, log the event, and redirect to dashboard
```

**Separated (preferred):**
```
WHEN a user submits valid credentials
THE SYSTEM SHALL authenticate the user

WHEN authentication succeeds
THE SYSTEM SHALL create a session with 24-hour expiry

WHEN a session is created
THE SYSTEM SHALL log the authentication event

WHEN authentication completes successfully
THE SYSTEM SHALL redirect to the dashboard
```

## Acceptance Criteria Checklist

Each EARS requirement should be:

- [ ] **Clear** - Unambiguous language
- [ ] **Testable** - Can write a test for it
- [ ] **Complete** - Specifies all conditions
- [ ] **Consistent** - No conflicts with other requirements
- [ ] **Traceable** - Links to user story
- [ ] **Feasible** - Technically achievable
