# Security Policy

## Supported Versions

Only the latest released version of this skill bundle receives security
updates. Install from the `main` branch or the newest tagged release.

| Version | Supported |
| ------- | --------- |
| latest release | yes |
| older tags | no |

## Reporting a Vulnerability

If you find a security issue in this repository (for example: a skill
instruction that could be abused for prompt injection, a script that
mishandles credentials, or an unsafe command pattern), please report it
privately:

- **Preferred:** open a private report via
  [GitHub Security Advisories](https://github.com/sergebulaev/linkedin-skills/security/advisories/new)
- **Alternative:** email `s@bulaev.org` with subject `[SECURITY] linkedin-skills`

Please include:

1. A description of the issue and where it lives (file path, skill name)
2. Steps to reproduce or a proof of concept
3. The impact you believe it has

You can expect an acknowledgement within 72 hours and a fix or a public
disclosure decision within 14 days.

## Scope notes

- This bundle never ships hardcoded credentials. API tokens (Apify,
  Publora) are read from environment variables or `.env` files that are
  gitignored; see `.env.example`.
- Scripts in `lib/` and `scripts/` perform HTTP calls only to the Apify,
  Publora and Pixfaro APIs, and never build a command from remote content.
  One code path does execute a command: the optional Tier 2 "DIY" backend
  runs whatever `LINKEDIN_SKILLS_CUSTOM_POSTER` names, via `subprocess`
  with no shell. That variable is unset by default; anything able to write
  it gains code execution on the next approved publish, so treat it as a
  credential. Set it only in the trusted launch environment; the bundle's
  `.env` loader accepts only API credentials and `LINKEDIN_PLATFORM_ID`, not
  custom commands or transport configuration. The CLI publishing scripts use
  the same restricted loader.
- Authenticated Publora calls, including credential diagnostics, refuse HTTP
  redirects so `x-publora-key` cannot travel to a different origin.
- Post deletion requires a successful status lookup showing `draft` or
  `scheduled`. Lookup errors and unknown, processing or live states stop the
  operation unless the caller explicitly passes `allow_live=True`. This is a
  client safeguard; the server must enforce the status check atomically to
  prevent a post changing state between the lookup and deletion.
- Content fetched from LinkedIn through the Apify read layer is untrusted
  input to the agent. See `references/untrusted-content.md`.
- Please do not test vulnerabilities against third-party services
  (LinkedIn, Apify, Publora) outside their own disclosure programs.
