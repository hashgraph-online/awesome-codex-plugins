# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| `main` | Yes |
| Latest published release | Yes |

## Reporting a Vulnerability

Please do not disclose security issues publicly before they have been reviewed.

To report a vulnerability, open a private report through GitHub Security Advisories for this repository, or email `dhairya15marwaha@gmail.com` with:

- a short description of the issue
- affected files, skills, commands, or plugin metadata
- reproduction steps or proof of concept details
- expected impact
- suggested fixes, if you already have them

We aim to acknowledge reports within 72 hours and follow up with an initial assessment as soon as practical.

## Security Practices

- Keep credentials, site tokens, bench secrets, and ERPNext/Frappe environment values out of plugin files.
- Review changes to skills and commands for prompt-injection risks before release.
- Run the plugin scanner workflow before publishing release artifacts.
- Prefer the latest published release when installing this plugin in day-to-day projects.
