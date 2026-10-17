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

## Trust boundary

Superloopy's evidence capture (`superloopy loop prove -- <command>`) **executes the command the agent chooses, with no allowlist and no sandbox, by design.** Reproducing a criterion means actually running its command, so the trust boundary is the agent (and the human) that decides what to run — not Superloopy. Commands run via `spawnSync` with an argv array and never through a shell (no `shell: true`), so there is no shell-injection surface, but the command itself is run as-is with the caller's privileges. Run Superloopy only on tasks and in environments where executing agent-selected commands is acceptable.

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
