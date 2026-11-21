# Authentication and session management (CWE-287, CWE-347, CWE-352, CWE-384, CWE-916, CWE-640, CWE-307)

## Sources
- Credentials, tokens and cookies: `Authorization`, session cookie, JWT claims (`alg`, `kid`, `jku`, `sub`, `role`), API keys, reset/verification tokens in URLs, OAuth `state`/`redirect_uri`/`code`.
- Request origin: cross-site form posts, `fetch` with `credentials: 'include'`, `Origin`/`Referer`/`Host` headers.
- Login/reset forms: username, email, phone, one-time codes (unbounded guesses).

## Sinks
| Concern | Sink / smell | Safe alternative |
| --- | --- | --- |
| JWT decode vs verify | `jwt.decode(t)` (node `jsonwebtoken`, PyJWT `options={"verify_signature": False}`), `jose` `decodeJwt` used for auth, claims trusted from `JSON.parse(atob(...))` | `jwt.verify(t, key, {algorithms:['RS256'], issuer, audience})`; fixed algorithm list from config |
| alg confusion / none | `algorithms` omitted or derived from the token header, one key shared between HS and RS, `kid` used as file path or SQL | pin algorithm per key; key looked up by `kid` from an allowlist; reject `none` |
| Password storage | `md5/sha1/sha256(password)`, unsalted, `crypto.createHash` for passwords, home-made KDF | `argon2id`, `bcrypt`, `scrypt`, PBKDF2 with high iterations; framework hasher (`password_hash`, Django `make_password`, Spring `PasswordEncoder`) |
| Password compare | `==`/`===` on hashes or tokens | constant-time: `crypto.timingSafeEqual`, `hmac.compare_digest`, `MessageDigest.isEqual`, `hash_equals` |
| Session fixation | session id kept across login; `session.id` accepted from URL | regenerate on login/privilege change: `req.session.regenerate`, Django `login()` cycles key, Rails `reset_session`, Spring `changeSessionId` (default) |
| CSRF | state-changing GET; cookie-authenticated POST/PUT/DELETE without token or `SameSite`; CSRF middleware disabled/excluded (`csrf_exempt`, `skip_before_action :verify_authenticity_token`, `.csrf().disable()` with cookie auth) | CSRF token (double-submit/synchronizer), `SameSite=Lax` or `Strict`, custom header requirement plus CORS that does not allow the origin |
| Reset flows | token = `Math.random`/timestamp/user id, no expiry, reusable, not bound to user, reset link built from `Host` header, account existence leaked, token logged | random >=128-bit token, store only a hash, single use, short expiry, invalidate sessions after reset, base URL from config |
| Brute force | login/OTP/reset endpoints without rate limit or lockout; per-IP only when attacker rotates; code of 4-6 digits without attempt counter | per-account and per-IP throttling, attempt counter on the code, uniform responses |
| Cookies | session cookie lacking `HttpOnly`, `Secure`, `SameSite` | set all three; `__Host-` prefix where it applies |

## Guards that work / Look-alike guards
Work:
- Signature verification with a pinned algorithm and key, plus `exp`, `iss`, `aud` validation, before any claim is used.
- Session regeneration on authentication state change.
- CSRF token validated server-side on every cookie-authenticated mutation, or authentication via an `Authorization` header that browsers do not attach automatically.
- Slow salted hash with parameters in config; constant-time compare.
- Rate limits keyed on the account identifier plus source; attempt counters on OTP.

Look-alike:
- `SameSite=Lax` as the only defense for a state-changing GET, or on sites that need cross-site POST flows; `SameSite=None` cookies.
- Checking the `Origin` header with `includes()`/`startsWith()`; accepting a missing `Origin`.
- CORS allowlist mistaken for CSRF protection (simple form posts are not blocked by CORS).
- JWT "verified" in a gateway but the service also accepts requests bypassing it; decoding for display then trusting claims.
- HS256 secret that is short/default/committed; shared secret across environments.
- SHA-256 with a salt for passwords; "peppered" MD5.
- Login rate limit on the UI only; or limit that resets on each failed attempt response.
- Reset token compared with `==` but otherwise random: low impact; do not over-report.

## Falsify before reporting
1. Is the token/cookie accepted for authentication at all on this path, or is it only decoded for non-security display?
2. Which verify call and options are used? Find the `algorithms` argument and key source.
3. CSRF: does the endpoint authenticate by cookie (ambient credential)? If it needs a bearer header set by JS, CSRF does not apply. Check global CSRF middleware and per-route exemptions, and `SameSite` default of the session config.
4. Is there a rate limiter in front (gateway, middleware, `express-rate-limit`, Rack::Attack, Spring filter) on THIS route? If infra is not in the repo, mark `needs-evidence`.
5. Password hash: is the value actually a password, or a high-entropy random API token where a fast hash is acceptable?
6. Confirm: tests with a token signed using `alg: none` / a different key are rejected; login changes the session id; a cross-origin POST without the token returns 403.

## Severity cues
- Raises: signature bypass (account takeover for any user), unauthenticated reset takeover, CSRF on email/password change or money movement, unsalted fast hashes in a store likely to leak.
- Lowers: CSRF on idempotent harmless action, brute force with strong per-account throttling, fixation needing prior cookie control on a Secure-only site, algorithm weaknesses mitigated by key length and pinned alg.

## Regression test
- Fails before: submit a token with the signature segment altered (or `alg: none`) to a protected route; assert 401 where before it returned 200.
- Expired and wrong-audience tokens rejected; a valid one accepted.
- Fixation: capture session id before login; assert it differs after login and the old id no longer works.
- CSRF: POST without the token (and with a foreign `Origin`) is rejected; with a valid token succeeds.
- Reset: a token is single use and expired token fails; allowed case: valid fresh token changes the password.
- Brute force: N+1 wrong attempts triggers throttling; correct credentials within limit still log in.
