# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| master  | ✅        |
| tags    | ✅        |

We support the latest release and the `master` branch. Older tags are archived as
read-only snapshots.

## Reporting a vulnerability

Please email **avivsinai@gmail.com** with "[bkt]" in the subject. Include:

- A detailed description of the issue and the potential impact
- Steps to reproduce (or proof of concept)
- Any temporary mitigations you are aware of

We will acknowledge receipt within two business days and provide regular status
updates until the issue is resolved.

If you require encrypted communication, request our PGP key in your initial
email.

## Disclosure policy

1. We investigate and confirm the vulnerability.
2. We coordinate a fix and target release date.
3. We publish a patched release and update the CHANGELOG with mitigation
   details.
4. Once a fix is available, we disclose the issue publicly.

## Dependencies

We rely on GitHub Dependabot, the OpenSSF Scorecard workflow, and the CI
workflows under `.github/workflows/` to keep dependencies fresh. See
[`docs/SECURITY.md`](docs/SECURITY.md) for deeper operational guidance.
