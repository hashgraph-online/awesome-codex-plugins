# Task Breakdown Strategies

Guidance for decomposing design into trackable implementation tasks.

## Core Principles

### Single Responsibility

Each task should accomplish one thing. If a task description contains "and", consider splitting it.

**Too broad:**
```
T-1: Implement user authentication and session management
```

**Better:**
```
T-1: Implement password hashing utility
T-2: Create user authentication endpoint
T-3: Implement JWT token generation
T-4: Create session management service
```

### Testable Completion

Every task must have clear acceptance criteria that can be verified.

**Vague:**
```
Acceptance: Authentication works
```

**Testable:**
```
Acceptance:
- POST /auth/login returns 200 with valid JWT for correct credentials
- POST /auth/login returns 401 for incorrect password
- JWT contains user ID and expiry claims
- Unit tests pass with >80% coverage
```

### Traceable to Requirements

Link tasks to requirements to ensure complete coverage.

```markdown
### T-3: Implement form validation

- **Requirements**: US-2 (Form Validation)
- **Description**: Add client-side validation for registration form
- **Acceptance**: All EARS criteria from US-2 pass manual testing
```

### Dependency Sequencing

Explicit dependencies enable parallel work and clear ordering.

```
T-1: Set up database schema        (no deps)
T-2: Create data models            (depends: T-1)
T-3: Implement repository layer    (depends: T-2)
T-4: Create API endpoints          (depends: T-3)
T-5: Write integration tests       (depends: T-4)
```

## Task Sizing

### Right-Sized Tasks

Tasks should be:
- **Not too small**: Avoid tasks like "Add import statement"
- **Not too large**: Avoid tasks taking multiple sessions
- **Completable**: Can finish and verify in one work session

### Size Guidelines

| Size | Description | Example |
|------|-------------|---------|
| XS | Single function/component | Add password validation regex |
| S | Small feature unit | Create login form component |
| M | Feature slice | Implement authentication flow |
| L | Consider splitting | Full user management system |

## Task Phasing

### Phase 1: Foundation

Setup tasks that enable all other work:

```markdown
## Phase 1: Setup

### T-1: Initialize project structure
- Status: pending
- Requirements: none (infrastructure)
- Description: Create project directories, initialize package.json, configure TypeScript
- Acceptance: `npm run build` succeeds with no errors
- Dependencies: none

### T-2: Configure development environment
- Status: pending
- Requirements: none (infrastructure)
- Description: Set up ESLint, Prettier, pre-commit hooks
- Acceptance: `npm run lint` runs without errors
- Dependencies: T-1

### T-3: Set up database connection
- Status: pending
- Requirements: US-1, US-2
- Description: Configure PostgreSQL connection, create migration system
- Acceptance: Can connect to database and run migrations
- Dependencies: T-1
```

### Phase 2: Core Implementation

Main feature functionality:

```markdown
## Phase 2: Core Implementation

### T-4: Create User data model
- Status: pending
- Requirements: US-1
- Description: Define User entity with fields from design doc
- Acceptance: Model validates correctly, migrations run
- Dependencies: T-3

### T-5: Implement user registration endpoint
- Status: pending
- Requirements: US-1
- Description: POST /api/users creates new user with validation
- Acceptance: Returns 201 with user object, 400 for invalid input
- Dependencies: T-4

### T-6: Implement authentication endpoint
- Status: pending
- Requirements: US-1
- Description: POST /api/auth/login validates credentials, returns JWT
- Acceptance: Returns 200 with JWT for valid credentials, 401 for invalid
- Dependencies: T-4
```

### Phase 3: Integration (MANDATORY)

This phase wires core implementation into the application. Every backend task from Phase 2 must have corresponding integration tasks here. Code that exists but isn't reachable is useless.

**Key question for each Phase 2 task: "Can a user reach this feature after Phase 2 alone?"** If not, add integration tasks.

```markdown
## Phase 3: Integration

### T-7: Wire login form to authentication endpoint
- Status: pending
- Wired: no
- Requirements: US-1
- Description: Connect login form submission to POST /api/auth/login. Display success/error states. Store JWT token. Redirect to dashboard on success.
- Acceptance: User can click "Login" button, enter credentials, submit form, and see dashboard (or error message)
- Dependencies: T-5, T-6

### T-8: Add dashboard route and navigation link
- Status: pending
- Wired: no
- Requirements: US-1
- Description: Register /dashboard route in router. Add "Dashboard" link to sidebar navigation. Protect route with auth middleware.
- Acceptance: Logged-in user can click "Dashboard" in sidebar and see the dashboard page. Unauthenticated users are redirected to login.
- Dependencies: T-6

### T-9: Wire user profile page to user API
- Status: pending
- Wired: no
- Requirements: US-2
- Description: Connect profile page to GET /api/users/:id endpoint. Render user data in profile component. Add "Profile" link to user menu.
- Acceptance: User can click their name in the header, select "Profile", and see their profile data loaded from the API.
- Dependencies: T-5, T-7
```

**Integration task naming convention:** Start with "Wire", "Connect", "Add [X] to [Y]", or "Register" to make wiring tasks immediately identifiable.

### Phase 4: Testing

Comprehensive test coverage:

```markdown
## Phase 4: Testing

### T-10: Write unit tests for auth service
- Status: pending
- Requirements: US-1
- Description: Unit tests for password hashing, JWT generation
- Acceptance: >80% coverage, all tests pass
- Dependencies: T-6

### T-11: Write integration tests for auth flow
- Status: pending
- Requirements: US-1
- Description: E2E tests for registration and login flows
- Acceptance: All happy paths and error cases covered
- Dependencies: T-7, T-8

### T-12: Write E2E tests for user journeys
- Status: pending
- Requirements: US-1, US-2
- Description: Playwright tests for complete user flows
- Acceptance: Tests run in CI, cover critical paths
- Dependencies: T-11
```

### Phase 5: Polish

Error handling, edge cases, documentation:

```markdown
## Phase 5: Polish

### T-13: Add error handling and logging
- Status: pending
- Requirements: US-1
- Description: Structured error responses, request logging
- Acceptance: All errors return consistent format, logs are searchable
- Dependencies: T-8

### T-14: Implement rate limiting
- Status: pending
- Requirements: US-1 (security)
- Description: Add rate limiting to auth endpoints
- Acceptance: Returns 429 after 5 failed attempts in 15 minutes
- Dependencies: T-6

### T-15: Add monitoring and alerts
- Status: pending
- Requirements: none (operational)
- Description: Set up APM, error tracking, alert rules
- Acceptance: Errors trigger alerts, dashboard shows metrics
- Dependencies: T-13
```

## Task Dependencies

### Dependency Types

**Hard dependency**: Cannot start until predecessor completes
```
T-4: Create User model
T-5: Create User repository (depends: T-4)  # Needs model first
```

**Soft dependency**: Can start but cannot finish until predecessor completes
```
T-6: Write API tests (soft-depends: T-5)  # Can write test stubs
```

### Dependency Visualization

```
T-1 (Setup)
 │
 ├──> T-2 (Dev env)
 │
 └──> T-3 (Database)
       │
       └──> T-4 (User model)
             │
             ├──> T-5 (Registration)──┐
             │                        │
             └──> T-6 (Auth)──────────┼──> T-7 (Frontend)
                                      │         │
                                      │         └──> T-8 (Protected routes)
                                      │                     │
                                      └─────────────────────┴──> T-9 (Tests)
```

## Claude Code Integration

### Syncing to Todos

After creating tasks.md, sync to Claude Code's todo system:

```
For each task:
  TaskCreate(
    subject: "T-{id}: {title}",
    description: "{full description with acceptance criteria}",
    activeForm: "{present tense action}"
  )

For dependencies:
  TaskUpdate(
    taskId: "{dependent task}",
    addBlockedBy: ["{blocking task ids}"]
  )
```

### Task Status Mapping

| tasks.md Status | Claude Code Status |
|-----------------|-------------------|
| pending | pending |
| in_progress | in_progress |
| completed | completed |

### Keeping in Sync

When updating task status:
1. Update tasks.md file (Status, Wired, and Verified fields)
2. Call TaskUpdate with new status
3. Summary count updates automatically

### Wired + Verified Tracking

The tasks.md summary table tracks both Wired and Verified counts:

| Status | Count |
|--------|-------|
| Completed | 8 |
| Wired | 6 |
| Verified | 5 |

This makes it immediately clear when tasks are "completed" but not actually working.

## Common Patterns

### Feature Flag Pattern

When feature needs gradual rollout:

```
T-1: Implement feature with flag disabled
T-2: Add feature flag configuration
T-3: Enable for internal users
T-4: Enable for beta users
T-5: Enable for all users
T-6: Remove feature flag
```

### Migration Pattern

When changing existing system:

```
T-1: Create new implementation alongside old
T-2: Add adapter/compatibility layer
T-3: Migrate data to new format
T-4: Switch traffic to new implementation
T-5: Verify metrics match expectations
T-6: Remove old implementation
```

### Testing Pyramid

```
T-N+0: Write unit tests (many, fast)
T-N+1: Write integration tests (some, medium)
T-N+2: Write E2E tests (few, slow)
```

## Task Template

```markdown
### T-{ID}: {Imperative title}

- **Status**: pending
- **Wired**: no | n/a
- **Verified**: no
- **Requirements**: {US-X, US-Y or "infrastructure"}
- **Description**: {Detailed description of what to implement}
- **Acceptance**:
  - {Specific, testable criterion 1}
  - {Specific, testable criterion 2}
- **Dependencies**: {T-X, T-Y or "none"}
- **Notes**: {Optional implementation hints or considerations}
```

### Wired Field Values

- `no` -- Code exists but is not connected to the application
- `yes` -- Code is reachable from the application's entry points (routes, navigation, API)
- `n/a` -- Task is infrastructure/config with nothing to wire (database setup, test writing, CI config)

### Task Lifecycle

```
pending → in_progress → completed (code written)
                         → Wired: yes (code connected to app)
                         → Verified: yes (tested end-to-end)
```

A task is only truly DONE when Status=completed AND Wired=yes/n/a AND Verified=yes.

## Anti-Patterns to Avoid

### Vague Tasks

**Bad:**
```
T-1: Make authentication work
```

**Good:**
```
T-1: Implement JWT authentication endpoint
- Acceptance: POST /auth/login returns valid JWT for correct credentials
```

### Hidden Dependencies

**Bad:**
```
T-3: Deploy to production (no dependencies listed, but actually needs T-1, T-2)
```

**Good:**
```
T-3: Deploy to production
- Dependencies: T-1, T-2
```

### Incomplete Coverage

Ensure all requirements map to tasks. Use a traceability matrix:

| Requirement | Tasks |
|-------------|-------|
| US-1 | T-4, T-5, T-6, T-9 |
| US-2 | T-7, T-8, T-10 |
| US-3 | T-11, T-12 |
