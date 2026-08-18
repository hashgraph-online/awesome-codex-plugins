# Cookies And Sessions

Cookies are a transport for session state, not a place to store credentials.

## Cookie Attributes

For session cookies:

- `HttpOnly`: true by default.
- `Secure`: true outside local development.
- `SameSite`: `Lax` for most server-rendered apps; use `Strict` only when the
  product flow tolerates it.
- `Path`: keep as narrow as practical.
- `Max-Age` or `Expires`: align with session policy.

Test `Set-Cookie` headers when adding auth flows.

## Session Storage

Prefer opaque session IDs backed by Redis, Postgres, or the framework's
server-side session store for privileged applications.

Signed client-side cookies are acceptable only when:

- The stored data is small and non-sensitive.
- The signing/encryption key is managed as a secret.
- Revocation requirements are understood.

## Login And Logout

- Renew or rotate session identifiers after login.
- Clear flash messages and transient auth state deliberately.
- Delete server-side session records on logout when applicable.
- Return redirects that match the product flow and do not create open redirects.

## Signed Messages

Flash messages and one-time notices can use signed cookies if they are not
secrets and expire quickly. Treat the signing key as a secret.
