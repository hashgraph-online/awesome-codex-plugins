---
name: htmx-security
description: Review and harden security for htmx and server-driven web apps. Use when handling user-supplied HTML, escaping or sanitizing fragments, adding CSP, evaluating XSS risk, configuring CSRF or cookies, loading htmx from a CDN, using SRI hashes, accepting hx-* attributes from content, or reviewing htmx request headers and history caching.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: htmx Security
  category: Frontend
  tags: htmx,security,xss,csp,frontend
---

# htmx Security

Use this skill before shipping htmx features that render user content, accept rich HTML, add third-party scripts, change Content Security Policy, or expose new mutation endpoints.

## Threat Model

htmx keeps rendering on the server, but unsafe HTML is still unsafe HTML. A fragment swap can insert scripts, event handlers, dangerous URLs, or htmx attributes that cause requests. Treat every fragment as executable browser surface unless it is escaped or sanitized.

## Baseline Rules

- Escape user-supplied text by default.
- Sanitize rich HTML on the server with a strict allowlist.
- Strip or block `hx-*`, `data-hx-*`, `hx-on`, inline event handlers, `script`, dangerous URLs, and style features that the product does not explicitly allow.
- Keep auth, authorization, and validation on the server.
- Use CSRF protection for same-origin mutations.
- Do not put secrets, privileged object IDs, or authorization decisions in HTML attributes.
- Keep htmx requests same-origin unless CORS, CSRF, cookies, and credentials are deliberately designed.

## User Content

Choose one content policy:

| User content type | Policy |
| --- | --- |
| Plain text | Escape and render as text |
| Markdown | Render through a sanitizer and allow only safe tags/attributes |
| Rich HTML | Sanitize with a narrow allowlist and strip htmx/event/script capabilities |
| Trusted admin HTML | Still sanitize unless the trust boundary is documented and access is tightly controlled |

Do not mark content safe merely because it was stored in the database earlier.

## htmx-Specific Risks

- User-controlled `hx-get`, `hx-post`, `hx-put`, `hx-patch`, `hx-delete`, or `hx-trigger` can create unintended requests.
- User-controlled `hx-on` or inline handlers can execute JavaScript.
- User-controlled `hx-vals` can smuggle unexpected parameters.
- Fragment responses can replace more of the page than intended if targets are broad.
- History caching can retain sensitive HTML on the client.

Use `hx-history="false"` on sensitive pages or containers that should not be stored in htmx history cache.

## CSRF And Cookies

- Prefer the framework's standard CSRF mechanism.
- Configure htmx to send the CSRF header once in the base layout or startup script.
- Keep CSRF tokens out of logs and analytics.
- Use `Secure`, `HttpOnly`, and `SameSite` cookie settings appropriate to the app.
- Avoid cross-site htmx mutations unless the app has a clear credential policy.

## CDN And Script Loading

Prefer vendored static assets for reproducibility. If loading htmx or extensions from a CDN:

- pin the exact version;
- include Subresource Integrity where possible;
- set `crossorigin` when required by SRI;
- document why CDN loading is acceptable for the app;
- monitor version changes deliberately rather than floating to latest.

## Content Security Policy

Design CSP around the actual frontend stack:

- htmx can work with a strict CSP when inline scripts and unsafe eval are avoided.
- Inline event handlers, `hx-on`, Alpine default builds, and `_hyperscript` can require looser policies unless replaced with CSP-compatible patterns.
- Start with report-only mode for existing apps, then tighten.
- Include reporting endpoints only when someone reviews reports.
- Test swapped fragments under the final CSP, not just the initial page load.

## Review Checklist

- Are all mutation endpoints protected by auth, authorization, and CSRF?
- Does every endpoint re-check permissions server-side?
- Are user values escaped in fragments and full pages?
- Is any rich content sanitized with an allowlist?
- Can user content inject `hx-*`, `hx-on`, event handlers, scripts, or dangerous URLs?
- Are sensitive fragments excluded from htmx history cache?
- Are third-party scripts pinned and integrity-checked?
- Does CSP match Alpine, `_hyperscript`, and htmx usage?
- Do tests cover both htmx and non-htmx paths?

## Testing Ideas

- Submit text containing HTML tags and confirm it renders as text.
- Submit sanitized rich content with attempted event handlers and htmx attributes.
- Attempt unauthorized htmx mutations directly with forged headers.
- Verify login redirects do not get swapped into small targets.
- Run browser checks with CSP enabled and inspect violations.

## Avoid

- Do not rely on htmx headers as proof of trust.
- Do not trust hidden inputs, `hx-vals`, or client-side state for authorization.
- Do not allow user-authored htmx attributes in normal rich content.
- Do not loosen CSP globally to fix one component without documenting the tradeoff.
- Do not expose JSON or HTML endpoints with different authorization assumptions.
