# Redirects, header injection and cross-origin policy (CWE-601, CWE-113, CWE-1021, CWE-942)

## Sources
- Redirect targets: `next`, `returnTo`, `redirect_uri`, `url`, `continue` params; `Referer`; post-login and logout flows; OAuth `redirect_uri`.
- Values placed in response headers: filename for `Content-Disposition`, `Location`, `Set-Cookie` values, custom headers echoing input.
- `Origin` header and `Access-Control-*` config; `X-Forwarded-Host`/`Host` used to build absolute links.

## Sinks
| Concern | Sink | Safe alternative |
| --- | --- | --- |
| Open redirect (601) | `res.redirect(req.query.next)`, `redirect(request.GET['next'])`, `redirect_to params[:url]`, `Response.Redirect`, `sendRedirect`, `header("Location: ".$x)`, `window.location = param` | relative-path allowlist (must start with a single `/`, not `//` or `/\`), or map keys to server-side URLs; parse with `new URL(x, base)` and compare `origin` |
| Header injection (113) | user value in `res.setHeader`, `Set-Cookie`, `Location`, `Content-Disposition` with CR/LF (modern frameworks usually reject CR/LF; verify the pinned one) | encode filename (`filename*=UTF-8''...`), reject control chars, framework helpers |
| CORS (942) | reflecting `Origin` into `Access-Control-Allow-Origin` together with `Access-Control-Allow-Credentials: true`; `origin: true` (Express `cors`), `allow_origins=["*"]` with credentials, `CORS_ORIGIN_ALLOW_ALL`, regex like `/example\.com/` unanchored; allowing `null` | static allowlist of exact origins; no credentials with wildcard (browsers also reject it) |
| Clickjacking (1021) | pages with state-changing UI (settings, payments, OAuth consent) served without frame protection | `Content-Security-Policy: frame-ancestors 'self'` (and `X-Frame-Options`) |
| Host header | password reset link or canonical URL from `Host`/`X-Forwarded-Host` | base URL from config; trusted proxy settings |

## Guards that work / Look-alike guards
Work:
- Redirect target restricted to a same-origin path after parsing, or looked up from a fixed table; applied at the redirect call itself.
- CORS origin compared by exact string match to a configured list; credentials only for those.
- `frame-ancestors` set globally with exceptions listed.
- Control-character rejection for any value used in a header; framework API that rejects newlines.

Look-alike:
- `url.startsWith('/')` (`//evil.example` and `/\evil.example` pass and browsers treat them as external).
- `url.includes('example.com')`, `endsWith('example.com')` (matches `evilexample.com`, `example.com.evil.test`), `startsWith('https://example.com')` (matches `https://example.com.evil.test`, and `@` userinfo tricks).
- Blocklisting `http://`/`https://` prefix while accepting `//host`, `javascript:` or scheme-relative forms.
- Redirect check on the login route but a second redirect after OAuth callback skipped.
- CORS regex without anchors/escaped dots; reflecting any origin because "no cookies are used" while an API key header or cookie is.
- CORS used as authorization: it only restricts browsers.
- `X-Frame-Options` on HTML only while an API-served HTML view is frameable.

## Falsify before reporting
1. Is the redirect target attacker-controlled and does it reach the `Location` header or `window.location` unmodified? Find the validation, if any, and test it against `//host`, `/\host`, and scheme tricks.
2. Is the open redirect combined with something that raises it (OAuth `redirect_uri` token leak, phishing from a trusted domain)? On its own it is usually low.
3. CORS: does the response set `Allow-Credentials: true`, and are the endpoints cookie-authenticated or return per-user data? Wildcard on a public, credential-less API is fine.
4. Header injection: does the runtime reject CR/LF in header values (Node `setHeader` throws `ERR_INVALID_CHAR`; check the stack pinned)? If yes, downgrade.
5. Clickjacking: does the framed page perform a sensitive one-click action? Report only then.
6. Confirm: validator unit test with `//example.test`, `/\example.test`, `https://example.test.evil.test`, plus CORS preflight with an unlisted `Origin` asserting no allow header.

## Severity cues
- Raises: redirect feeding OAuth/SSO flows, credentialed CORS reflecting arbitrary origins with per-user data, header injection enabling cookie setting or response splitting on a proxy that does not filter.
- Lowers: plain open redirect after login (low), CORS without credentials on public data, clickjacking on read-only pages, modern servers that block CR/LF.

## Regression test
- Fails before: GET `/login?next=//example.test` and assert the response `Location` is not external; after the fix it is the default path.
- Subdomain trick: `next=https://allowed.example.test.evil.test/` rejected; `next=/dashboard?x=1` still redirects.
- CORS: request with `Origin: https://not-listed.test`; assert no `Access-Control-Allow-Origin` and no credentials header; a listed origin gets exact echo.
- Header: filename containing `a\r\nX-Test: 1` yields a rejected request or an encoded header; ordinary unicode filename downloads fine.
