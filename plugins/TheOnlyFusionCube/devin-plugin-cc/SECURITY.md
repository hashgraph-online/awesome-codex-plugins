# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security reports. Instead:

- Use [GitHub private vulnerability reporting](https://github.com/TheOnlyFusionCube/devin-plugin-cc/security/advisories/new), or
- Open an issue describing the affected area without exploit details and ask for a private channel.

We aim to acknowledge reports within 7 days.

## Scope

This repository shells out to the locally installed `devin` CLI and calls the Devin API with `DEVIN_API_KEY`. It never writes credentials to disk. Reports are most useful for: command injection through prompt/flag arguments, unintended file writes outside the job state directory, secret leakage into logs or artifacts, and unsafe hook behavior.

## Supported versions

Only the latest release on `main` receives fixes.
