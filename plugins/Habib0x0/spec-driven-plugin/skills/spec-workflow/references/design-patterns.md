# Design Documentation Patterns

Guidance for creating comprehensive technical design documents.

## Architecture Documentation

### Component Diagram

Use ASCII or Mermaid diagrams to show system components:

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   Auth   │  │  Dashboard│  │ Settings │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                      │
│       └─────────────┼─────────────┘                      │
│                     │                                    │
└─────────────────────┼────────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────┼────────────────────────────────────┐
│                     │           API Gateway              │
│              ┌──────┴──────┐                             │
│              │   Router    │                             │
│              └──────┬──────┘                             │
│       ┌─────────────┼─────────────┐                      │
│       │             │             │                      │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐                 │
│  │Auth Svc │  │User Svc │  │Data Svc │                 │
│  └────┬────┘  └────┬────┘  └────┬────┘                 │
└───────┼────────────┼────────────┼────────────────────────┘
        │            │            │
┌───────┼────────────┼────────────┼────────────────────────┐
│       │            │            │        Data Layer      │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐                 │
│  │  Redis  │  │PostgreSQL│  │   S3   │                 │
│  └─────────┘  └─────────┘  └─────────┘                 │
└──────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

Show how data moves through the system:

```
User Input → Validation → Processing → Storage → Response

[Browser] --POST /api/users--> [API Gateway]
    [API Gateway] --validate--> [Auth Service]
    [Auth Service] --JWT--> [API Gateway]
    [API Gateway] --create--> [User Service]
    [User Service] --INSERT--> [PostgreSQL]
    [PostgreSQL] --user_id--> [User Service]
    [User Service] --user object--> [API Gateway]
[API Gateway] --201 Created--> [Browser]
```

## Component Specification Template

```markdown
### ComponentName

**Purpose**: One-sentence description of why this component exists

**Responsibilities**:
- Primary responsibility
- Secondary responsibility
- What it owns/manages

**Interfaces**:
- **Input**: What data/events it receives
- **Output**: What data/events it produces
- **Dependencies**: Other components it relies on

**Internal Structure** (if complex):
- Subcomponent A - purpose
- Subcomponent B - purpose

**State Management**:
- What state it maintains
- How state is persisted (if applicable)

**Error Handling**:
- How it handles failures
- Retry strategies
- Fallback behavior
```

## Data Model Documentation

### Entity Definition

```markdown
### User

**Purpose**: Represents a registered user in the system

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| email | string | unique, not null | User's email address |
| password_hash | string | not null | Bcrypt hash of password |
| created_at | timestamp | not null, default now | Creation time |
| updated_at | timestamp | not null | Last modification time |
| deleted_at | timestamp | nullable | Soft delete marker |

**Relationships**:
- Has many: Sessions, AuditLogs
- Belongs to: Organization (optional)

**Indexes**:
- email (unique)
- created_at (for sorting)
- organization_id (for filtering)

**Constraints**:
- Email must be valid format
- Password hash must be 60 characters (bcrypt)
```

### Type Definitions

```typescript
interface User {
  id: string;           // UUID v4
  email: string;        // Valid email format
  passwordHash: string; // Bcrypt hash
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;     // Soft delete
}

interface CreateUserRequest {
  email: string;
  password: string;     // Min 8 chars, 1 upper, 1 number
}

interface UserResponse {
  id: string;
  email: string;
  createdAt: string;    // ISO 8601
}
```

## API Design Documentation

### Endpoint Specification

```markdown
### Create User

**Method**: POST
**Path**: /api/v1/users
**Authentication**: None (public endpoint)

**Request Headers**:
| Header | Required | Description |
|--------|----------|-------------|
| Content-Type | Yes | Must be application/json |

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Validation**:
- email: Required, valid email format, max 255 chars
- password: Required, min 8 chars, 1 uppercase, 1 number

**Success Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:
| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid input data |
| 409 | EMAIL_EXISTS | Email already registered |
| 500 | INTERNAL_ERROR | Server error |

**Error Body**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      { "field": "email", "message": "Must be a valid email" }
    ]
  }
}
```
```

## Sequence Diagrams

### Mermaid Format

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant S as Auth Service
    participant D as Database

    U->>F: Enter credentials
    F->>A: POST /auth/login
    A->>S: Validate credentials
    S->>D: Query user by email
    D-->>S: User record
    S->>S: Verify password hash
    S->>S: Generate JWT
    S-->>A: JWT + refresh token
    A-->>F: 200 OK + tokens
    F->>F: Store tokens
    F-->>U: Redirect to dashboard
```

### ASCII Format

```
User          Frontend       API Gateway    Auth Service   Database
 │               │               │               │            │
 │──credentials─>│               │               │            │
 │               │──POST /login─>│               │            │
 │               │               │──validate────>│            │
 │               │               │               │──query────>│
 │               │               │               │<──user─────│
 │               │               │               │            │
 │               │               │<──JWT────────│            │
 │               │<──200 + JWT───│               │            │
 │<──redirect────│               │               │            │
 │               │               │               │            │
```

## Security Considerations Template

```markdown
## Security Considerations

### Authentication
- Method: JWT with RS256 signing
- Token expiry: 15 minutes (access), 7 days (refresh)
- Storage: HttpOnly cookies (refresh), memory (access)

### Authorization
- Model: Role-based access control (RBAC)
- Roles: admin, user, guest
- Permission checks at API gateway level

### Data Protection
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- PII handling: Anonymized in logs

### Input Validation
- All inputs sanitized against XSS
- SQL injection prevented via parameterized queries
- File uploads scanned for malware

### Rate Limiting
- API: 100 requests/minute per IP
- Auth endpoints: 5 requests/minute per IP
- Websocket: 50 messages/second per connection
```

## Performance Considerations Template

```markdown
## Performance Considerations

### Targets
- API response time: < 200ms (p95)
- Page load time: < 2s (first contentful paint)
- Database queries: < 50ms

### Caching Strategy
- Static assets: CDN with 1-year cache
- API responses: Redis with 5-minute TTL
- Database: Query result caching

### Scalability
- Horizontal scaling: Stateless services behind load balancer
- Database: Read replicas for query distribution
- Background jobs: Queue-based processing

### Monitoring
- APM: Response times, error rates, throughput
- Database: Query performance, connection pool
- Infrastructure: CPU, memory, disk I/O
```

## Alternatives Considered Template

```markdown
## Alternatives Considered

### Alternative 1: [Name]

**Description**: Brief description of the alternative

**Pros**:
- Advantage 1
- Advantage 2

**Cons**:
- Disadvantage 1
- Disadvantage 2

**Decision**: Not chosen because [specific reason]

### Alternative 2: [Name]

**Description**: Brief description

**Pros**:
- Advantage 1

**Cons**:
- Disadvantage 1

**Decision**: Not chosen because [specific reason]
```
