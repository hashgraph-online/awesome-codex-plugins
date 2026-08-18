# Auth Middleware And Typed Access

Route protection should be centralized and visible in tests.

## Guard Boundary

Use the framework's middleware, extractor, or guard mechanism to turn session
state into a typed authenticated user:

```rust
pub struct AuthenticatedUser {
    pub user_id: uuid::Uuid,
}
```

Handlers that require auth should accept `AuthenticatedUser`, not
`Option<AuthenticatedUser>`.

## Checks

- Authentication: is there a valid session or token?
- Authorization: is this authenticated identity allowed to perform this action?
- Freshness: does this operation require recent password verification?
- CSRF: do cookie-authenticated mutating requests have CSRF protection?

## Tests

- Unauthenticated requests are rejected or redirected.
- Authenticated users can access allowed routes.
- Authenticated but unauthorized users are rejected.
- Session tampering or unknown session IDs fail closed.
- Middleware preserves request data needed by downstream handlers.
