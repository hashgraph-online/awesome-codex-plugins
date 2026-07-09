# Secrets And PII

Treat observability as a data exposure surface. A trace field, panic message, or
debug dump can leak the same information as an API response.

## Never Log Raw

- Passwords or password reset tokens.
- Session IDs and signed cookie contents.
- Bearer tokens, API keys, OAuth codes, and refresh tokens.
- Full payment data.
- Password hashes unless the project explicitly treats them as safe diagnostic
  data; default to not logging them.

## Use Secret Types

Use `secrecy::SecretString` or a project-local wrapper when a value should not
appear in `Debug` output:

```rust
use secrecy::{ExposeSecret, SecretString};

pub struct Credentials {
    pub username: String,
    pub password: SecretString,
}

verify_password(credentials.password.expose_secret(), stored_hash).await?;
```

Expose secrets only at the call site that needs the raw value.

## Redaction Pattern

When logs need a stable correlation value, log a derived non-secret:

- User ID instead of email when possible.
- Domain name instead of full email.
- Last four characters only when product policy permits it.
- Hash of a token only when the hash cannot be used as a credential.

## Error Messages

User-facing errors should be specific enough to act on but not specific enough
to enumerate users, credentials, or resources. Operator-facing errors can carry
more context through spans and secure logs.
