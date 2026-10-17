# Security policy

## Supported version

Security fixes are applied to the latest release on the default branch.

## Reporting a vulnerability

Use this repository's private vulnerability-reporting form. Do not place credentials, private memory, account identifiers, working exploits, or another user's local paths in a public issue.

Revoke any exposed TMCRA credential immediately. Include only the affected plugin, Codex or Claude Code version, operating system, reproduction steps, and the smallest redacted diagnostic sample.

## Security boundary

- Production API origins require HTTPS; explicit localhost endpoints are accepted for development and tests.
- Normal installation uses browser device authorization and writes the scoped credential to a protected local configuration file.
- Credentials, device codes, PKCE verifiers, delivery receipts, private keys, verification codes, developer instructions, and chain-of-thought are excluded from memory and logs.
- Recalled material is marked as untrusted evidence. Current user instructions retain higher authority.
- Automatic lifecycle hooks use short timeouts and fail open so a memory-service outage cannot block the host Agent.
- User, assistant, tool, session, project, and Agent provenance remain distinct.

The hosted TMCRA service, account console, deployment infrastructure, and other integrations have their own security boundaries.
