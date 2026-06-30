# Security Policy

## Supported Versions

Security fixes are accepted for the latest version on the `main` branch.

## Reporting a Vulnerability

Please do **not** open a public issue with exploit details or sensitive information.

Use GitHub's private vulnerability reporting for this repository if it is available. If private reporting is unavailable, open a minimal public issue asking for a private contact path, without including exploit details, secrets, or proof-of-concept payloads.

A good report includes:

- Affected version or commit SHA.
- The vulnerable component or workflow.
- Reproduction steps that avoid exposing real secrets or third-party systems.
- Expected impact and any known mitigations.

I will acknowledge valid reports as soon as practical, investigate, and publish a fix or mitigation note when appropriate.

## Scope

In scope:

- The Superloopy CLI and bundled plugin files.
- Repository-local evidence/state handling under `.superloopy/`.
- Codex hook configuration shipped by this repository.

Out of scope:

- Social engineering.
- Denial-of-service reports that rely only on excessive local resource consumption.
- Vulnerabilities in third-party tools unless Superloopy's integration materially changes their risk.

## No Bug Bounty

This project does not currently run a paid bug bounty program.
