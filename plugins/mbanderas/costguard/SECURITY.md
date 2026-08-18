# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities privately. **Do not open a public
issue for a suspected vulnerability.**

- Preferred: open a [private security advisory](https://github.com/mbanderas/costguard/security/advisories/new)
  via GitHub's "Report a vulnerability" flow.
- Alternative: email **markbanderas@gmail.com** with the details.

Please include:

- A description of the issue and its impact.
- Steps to reproduce (proof-of-concept where possible).
- Affected version(s) and environment.

You can expect an acknowledgement within 5 business days and a remediation
plan or status update within 30 days. Please give us a reasonable window to
ship a fix before any public disclosure.

## Supported Versions

The latest published release on the `master` branch receives security
updates. Older versions are not maintained.

## Security Posture

Costguard is designed to be safe to run anywhere:

- **Read-only provider access.** No write or mutating API call is ever issued
  against provider accounts.
- **Secrets stay out of the repo.** Provider tokens are read only from the
  process environment or a gitignored `.env`; they are never printed, logged,
  or committed.
- **Outward actions are inert and gated.** `fix --open-pr` and `digest --post`
  refuse to act without an explicit opt-in flag and the matching credential,
  and perform no git push or network post in this build.

See the [README](README.md#security--read-only-posture) for the full posture.
