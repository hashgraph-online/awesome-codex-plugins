# Security Policy

Superpipelines coordinates agents that can read, write, and run commands through host tools. Security reports are taken seriously, especially anything that widens reviewer permissions, bypasses sandbox expectations, or causes agent-controlled execution outside the documented scope.

## Supported versions

Security fixes target the current release line on `main`. Older unreleased branches may be updated when they are still open as active PRs.

## Reporting a vulnerability

Use GitHub private vulnerability reporting if it is enabled for this repository. If it is not available, open a minimal public issue that says a security report exists, without exploit details, and request a private contact path.

Please include:

- Affected platform and host version.
- The command or pipeline path used to reproduce the issue.
- Whether the host session was sandboxed, workspace-write, read-only, or danger-full-access.
- Expected enforcement behavior and observed behavior.
- Logs or transcripts, with secrets removed.

## Scope

In scope:

- Reviewer write-deny bypasses.
- Materialized agent files granting broader tools than their CAD capabilities.
- Installer behavior that fetches or executes unexpected code.
- Pipeline state corruption that can cause unsafe re-execution.
- Documentation claims that overstate enforcement for a platform.

Out of scope:

- Model quality issues without a permissions, state, or installer impact.
- Vulnerabilities in host tools unless Superpipelines widens or hides the host behavior.
- Social engineering reports without a concrete repository or runtime path.

## Disclosure posture

If a reported issue invalidates a public safety claim, the fix should include both the code or documentation change and a short verification transcript. The project prefers honest degradation warnings over unverifiable security claims.
