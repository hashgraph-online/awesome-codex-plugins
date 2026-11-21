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
instruction that could be abused for prompt injection, or an unsafe command
pattern), please report it privately:

- **Preferred:** open a private report via
  [GitHub Security Advisories](https://github.com/sergebulaev/exotic-car-rental-skills/security/advisories/new)
- **Alternative:** email `s@bulaev.org` with subject `[SECURITY] exotic-car-rental-skills`

Please include a description and where it lives (file path, skill name), steps
to reproduce, and the impact you believe it has. You can expect an
acknowledgement within 72 hours and a fix or a public disclosure decision within
14 days.

## Scope notes

- This bundle uses no credentials. There is no `.env`, no API key and no token.
- `lib/carrentallist_client.py` makes HTTPS POST requests to one host,
  `mcp.carrentallist.com`, with the Python standard library. It refuses
  redirects, never executes shell commands and never writes files.
- The catalog server is public and read-only. Skills send it only search
  arguments (city, make, model, price filters), never the user's documents,
  customer data or reviews.
- Text from reviews, emails, competitor listings and catalog descriptions is
  handled as data, never instructions (`references/untrusted-content.md`,
  enforced by `scripts/check_untrusted_rule.py`).
