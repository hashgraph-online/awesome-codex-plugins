# Security Policy

## Supported Versions

Only the latest version on the `main` branch is actively supported. Security fixes are released through normal repository updates.

## Reporting a Vulnerability

If you discover a security vulnerability in Spellbook Skills, do not open a public issue first. Report it by email to `code4j@code4j.site` with enough detail for reproduction and triage.

Please include:

- A short description of the issue
- The affected skill, hook, script, or manifest
- Steps to reproduce, if applicable
- Relevant scanner output, logs, or command output
- Any known impact or workaround

Reports are reviewed as soon as practical. Confirmed vulnerabilities will be fixed in the repository and noted in the relevant release or pull request.

## Scope

Security reports are especially useful for:

- Hardcoded secrets or accidental credential exposure
- Unsafe shell, PowerShell, or Python execution paths
- Plugin manifest or marketplace packaging issues
- Hook behavior that can run unexpectedly or bypass user intent
- Supply-chain risks in CI, installer, or scanner configuration
