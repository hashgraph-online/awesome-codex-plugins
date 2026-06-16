---
name: rust-service-security
description: Use when adding, changing, testing, or reviewing security-sensitive Rust web service behavior, especially login flows, password hashing, credential checks, session cookies, flash messages, admin route protection, auth middleware, user enumeration defenses, or moving CPU-heavy password work off async executors.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Service Security
  category: Rust
  tags: rust,security,authentication,sessions,passwords
---

# Rust Service Security

Use this skill when a Rust service handles identity, credentials, sessions,
cookies, privileged routes, or sensitive user data. Prefer explicit threat
checks and tests over optimistic handler code.

## Core Workflow

1. Identify the protected asset: account access, admin area, session state,
   password change, reset token, private data, or privileged operation.
2. Trace the whole flow: request parsing, credential lookup, verification,
   session mutation, redirects/responses, logs, and tests.
3. Keep secrets out of logs and debug output. Use secret wrappers for passwords,
   tokens, signing keys, and session secrets.
4. Run password hashing and verification with memory-hard algorithms and move
   CPU-heavy work off async reactor threads.
5. Prevent user enumeration. Failed login and password reset flows should not
   reveal whether the account exists.
6. Set cookie and session attributes deliberately: `HttpOnly`, `Secure`,
   `SameSite`, path, lifetime, signing/encryption, and store backend.
7. Protect routes at middleware or extractor boundaries, not by repeating
   ad-hoc checks in every handler.
8. Add tests for happy path, failed auth, missing session, forged cookie or
   token, and logout/session rotation behavior.

## Password Rules

Read `references/password-auth.md` before implementing or changing password
storage or verification.

- Store PHC strings produced by Argon2id or the project's chosen password
  hasher; never store plaintext or reversible encrypted passwords.
- Generate salts with a secure RNG.
- Use constant, generic responses for invalid credentials.
- Use `tokio::task::spawn_blocking` or a dedicated blocking abstraction for
  expensive password operations.
- Keep password hash parameters configurable enough to upgrade over time.

## Cookie And Session Rules

Read `references/cookies-sessions.md` when setting, reading, deleting, signing,
or persisting cookies and sessions.

- Never store raw credentials in cookies.
- Prefer opaque session IDs backed by a server-side store for privileged apps.
- Rotate or renew session state after login and privilege changes.
- Delete sessions server-side on logout when using a server-side store.
- Test security attributes on `Set-Cookie` headers.

## Route Protection

Read `references/auth-middleware.md` when adding admin routes, extractors,
guards, or framework middleware.

Keep handlers typed:

```rust
pub async fn admin_dashboard(user: AuthenticatedUser) -> Result<HttpResponse, AppError> {
    // Handler can assume authentication succeeded.
    Ok(HttpResponse::Ok().finish())
}
```

Avoid optional user lookups in handlers that require authentication; make the
missing-user case impossible at the handler signature when the framework allows
it.

## Reference Files

- `references/password-auth.md`: Argon2, PHC strings, user enumeration, and
  blocking password work.
- `references/cookies-sessions.md`: cookie flags, signed messages, server-side
  sessions, and logout.
- `references/auth-middleware.md`: route guards, extractors, and typed session
  access.
