# Password Authentication

Password code is security-critical and performance-sensitive. Keep it small,
tested, and isolated from handlers.

## Storage

- Store a PHC string from a memory-hard password hasher such as Argon2id.
- Do not store plaintext passwords, reversible encrypted passwords, or separate
  salt columns unless the chosen hasher requires it.
- Treat password hashes as sensitive operational data. Avoid logging them.

## Verification Boundary

```rust
pub async fn verify_password(
    candidate: secrecy::SecretString,
    expected_hash: secrecy::SecretString,
) -> Result<bool, anyhow::Error> {
    tokio::task::spawn_blocking(move || {
        verify_password_blocking(candidate, expected_hash)
    })
    .await?
}
```

Use `spawn_blocking` or an equivalent blocking worker boundary because password
hashing is CPU and memory intensive.

## User Enumeration

Login and reset flows should not reveal whether an account exists.

Patterns:

- Return the same response for missing user and wrong password.
- Consider a fake password hash for missing users so timing does not trivially
  reveal account existence.
- Log safe diagnostic fields internally, not raw credentials.

## Tests

- Valid password succeeds.
- Wrong password fails.
- Missing user returns the same public response as wrong password.
- Password hash verification does not run on the async reactor directly when
  the project has an abstraction for blocking work.
