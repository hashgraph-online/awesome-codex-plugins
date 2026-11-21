# Block Signals

> Recognize a challenge, a failed sensor, or a stub from the response itself, and know which WAF products need a real browser.

## 1. Challenge Markers

A body or title that contains one of these is a `challenge`, whatever the status code.

| Product family | Body or title markers | Cookie or header signals | Needs a real browser |
|---|---|---|---|
| Cloudflare | `Just a moment...`, `Checking your browser`, `cf-chl-`, `Attention Required! \| Cloudflare` | `cf-ray`, `server: cloudflare`, `__cf_bm`, `cf_clearance` | `needs_js` (a browser engine passes; real TLS not required) |
| Akamai Bot Manager | `sec-if-cpt-container`, `Powered and protected by Akamai`, `Access Denied` with a reference number | `_abck`, `bm_sz`, `ak_bmsc`, `server: AkamaiGHost` | `needs_real_browser` (real TLS stack and JavaScript sensor) |
| DataDome | `DataDome`, `captcha-delivery.com` | `datadome` cookie | `needs_real_browser` |
| HUMAN (PerimeterX) | `px-captcha`, `Press & Hold to confirm you are a human` | `_px3`, `_pxhd`, `_px2` | `needs_real_browser` |
| F5 BIG-IP ASM | `The requested URL was rejected`, `support ID is:` | `BigIPServer*`, `TS01*` | `needs_real_tls` |
| AWS WAF | Challenge or CAPTCHA page from `awswaf` | `aws-waf-token`, `x-amzn-waf-*` | `needs_real_tls` |
| Unknown | A short page asking to enable JavaScript or cookies, or a CAPTCHA widget | none | Treat as `needs_js` |

Detect the product with at least two signals before trusting its row; one signal gives a tentative match. The rows describe products, never sites.

## 2. Failed-Sensor State

| Signal | Meaning |
|---|---|
| `_abck` value containing `~-1~` | Akamai sensor not completed |
| `cf_clearance` absent after a Cloudflare challenge page | Challenge not passed |
| A `Set-Cookie` for a WAF cookie plus a body under 3 KB | Challenge served, content withheld |
| A 200 whose body equals the size of a challenge page seen earlier in the same run | Same challenge, different status |

## 3. Stubs

| Stub | How to recognize it |
|---|---|
| Redirect page | Under 3 KB with `<meta http-equiv="refresh">` or a `location` script, pointing back to the blocked host |
| Search interstitial | Title `Google Search` or another search home on a cache URL; Google's web cache ended in 2024 and its URL now returns the search interstitial (observed 2026-11-07: HTTP 200, 93,735 bytes, title `Google Search`) |
| Empty JavaScript shell | A root element such as `<div id="root"></div>` or `<div id="__next"></div>` with no text, and script tags only |
| Consent wall | A cookie-consent page that hides the content until a choice is made |
| AMP cache redirect | A short `Redirecting` page on an AMP cache host that sends the client back to the origin |
| Challenge body on an archive host | An archive response whose body is a challenge page instead of the snapshot (seen once on a rewritten `web/<ts>/<url>` view on 2026-11-07, not reproduced minutes later); change one axis: the raw `web/<ts>id_/<url>` path or another snapshot timestamp |

## 4. Status Codes

| Status | First reading | Next step |
|---|---|---|
| 401 | Authentication required | `rules/access-policy.md` §2 unless the account is the user's |
| 403 | Refused; often a client filter, sometimes a real ban | Check the body markers; a challenge body means tier 1 retry axes, a plain refusal after normal browsing means §2 |
| 407 | Proxy authentication | The network, not the site; report it |
| 429 | Rate limited | Honor `Retry-After`; never retry immediately |
| 451 | Legal block | Outside the boundary |
| 503 with a challenge body | Challenge, not an outage | Treat as `challenge` |
| 000 or connection reset | No response from this network | Record; try the next archive or tier, not the same request again |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Product markers, cookie families, and real-TLS needs | The `ultimate-browsing` skill in `code-yeongyu/oh-my-openagent` (branch `dev`), read 2026-11-07 |
| Google Cache interstitial and AMP redirect stubs | the same skill, plus a probe from this repository's network on 2026-11-07 |
| `server: cloudflare` and `cf-ray` headers on a Cloudflare host | probe of `https://www.cloudflare.com/` on 2026-11-07 |
| Status code meanings | RFC 9110, <https://www.rfc-editor.org/rfc/rfc9110.html>; RFC 6585; RFC 7725 |
| The two-signal rule and the stub list | this package's chosen design, not a validated optimum |
