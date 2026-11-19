# Server-side request forgery (CWE-918)

## Sources
- URL/host fields: webhook target, avatar/import-by-URL, link preview/unfurl, feed/RSS import, OAuth/OIDC discovery URL, "test connection" for a DB/S3/SMTP endpoint, PDF/HTML-to-image renderers, image `src` rendered server-side.
- File content with URLs: SVG/HTML/XML (`xlink:href`, XXE), Markdown, OpenAPI specs, git remotes, package URLs.
- Headers that choose a host: `Host`, `X-Forwarded-Host`, `Origin`, used to build callbacks.
- Redirect responses from a URL the attacker controls (a fetch that follows to an internal target).

## Sinks
| Stack | Fetch API (sink) | Safer pattern |
| --- | --- | --- |
| Node | `fetch`, `axios.get(url)`, `got`, `http.get`, `request`, `puppeteer.goto`, `playwright page.goto` | resolve + validate IP, then connect to that IP; `redirect:'manual'`; egress proxy |
| Python | `requests.get`, `httpx`, `urllib.request.urlopen` (also `file:`/`ftp:`), `aiohttp` | validate scheme/IP, `allow_redirects=False`, pin resolved IP via custom adapter/transport |
| Java | `URL.openConnection`, `HttpClient`, `RestTemplate`, `WebClient`, `ImageIO.read(URL)` | resolve and check `InetAddress` (`isSiteLocal`, `isLoopback`, `isLinkLocal`, `isAnyLocal`) before connecting; custom DNS resolver |
| Go | `http.Get(url)`, `http.Client` default | `net.Dialer.Control` hook that rejects non-public IPs at connect time; `CheckRedirect` |
| Ruby | `Net::HTTP`, `open-uri` `URI.open(url)`, `Faraday` | same checks; avoid `URI.open` with user-supplied strings |
| PHP | `file_get_contents(url)`, `curl_exec`, `fopen` wrappers | `CURLOPT_PROTOCOLS`, `CURLOPT_FOLLOWLOCATION` off, IP check on resolved address |

## Guards that work / Look-alike guards
Work:
- Parse with a real URL parser, require `https`/`http` scheme, compare parsed `hostname` exactly (or by suffix with a leading dot) against an allowlist.
- Resolve the name, reject loopback, link-local (169.254.0.0/16 incl. metadata), private (RFC1918), CGNAT, unspecified, multicast, and IPv6 equivalents (`::1`, `fc00::/7`, `fe80::/10`, IPv4-mapped `::ffff:a.b.c.d`), then connect to that same IP (no second lookup) or enforce the rule in the dialer.
- Redirects disabled, or each hop re-validated with the same function.
- Network-level egress policy or dedicated fetch proxy; cloud metadata v2/hop limit as defense in depth.
- A server-side lookup by id from a fixed table instead of a user-supplied URL.

Look-alike:
- `url.startsWith("https://allowed.com")` (also matches `https://allowed.com.evil.test` and `https://allowed.com@evil.test`); `includes`, `endsWith("allowed.com")` without a dot.
- Regex on the string for `localhost|127\.0\.0\.1` (misses `0.0.0.0`, `[::1]`, decimal/octal/hex forms such as `2130706433`, `0x7f.1`, `017700000001`, IPv4-mapped IPv6, and DNS names resolving to private IPs).
- Resolve-then-fetch with two lookups (DNS rebinding / TOCTOU between check and use).
- Validating the first URL but following redirects.
- Allowlist applied to the `Host` header or to a different field than the one fetched.
- Blocking only metadata IP while other internal ranges stay reachable.
- Client-side URL check.

## Falsify before reporting
1. Is the URL (or any part of host/port/scheme) attacker-controlled, or built from config and a validated id?
2. Does the server follow redirects, and does validation run per hop?
3. Does validation use a parsed hostname and a resolved-IP check on the same connection, or string operations?
4. Is there a network egress policy or fetch proxy visible in infra code in this repo? If not visible: `needs-evidence` with that as the deciding fact.
5. Is the response returned to the attacker (full read), only status/timing (blind), or discarded? Sets severity.
6. Confirm: a unit test of the validator with benign values `http://169.254.169.254/`, `http://[::1]/`, `http://2130706433/` and `https://allowed.com.example.test/` asserts rejection.

## Severity cues
- Raises: unauthenticated or self-service actor, cloud metadata reachable, response body returned, non-HTTP schemes allowed, internal admin services on the network.
- Lowers: blind only, admin-only configuration, fetch runs in an isolated egress-restricted worker, HTTPS-only with allowlisted hosts.

## Regression test
- Fails before: submit the benign internal values above to the real endpoint (HTTP client mocked to record the target) and assert 4xx and no outbound call.
- Redirect case: a mock allowed host returns 302 to `http://169.254.169.254/`; assert it is not followed.
- Allowlist boundary: `https://allowed.com.example.test` and `https://allowed.com@example.test` rejected.
- Allowed case: a legitimate public HTTPS host on the allowlist fetches normally, including a redirect to another allowlisted host.
