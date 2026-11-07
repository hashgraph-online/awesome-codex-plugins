# Security Policy

## Supported Versions

Bifrost is in active development against `main`. Only `main` is supported
at this time — there are no LTS branches. If you're running a fork or a
historical commit, please rebase onto current `main` before reporting.

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |
| Older   | :x:                |

## Reporting a Vulnerability

**Do not open a public issue for security reports.**

Two ways to report privately:

### 1. GitHub private vulnerability reporting (preferred)

Submit a draft advisory through [GitHub's private vulnerability reporting](https://github.com/gobifrost/bifrost/security/advisories/new).
This keeps the report confidential and lets us discuss + patch + coordinate
disclosure inside GitHub's tooling.

### 2. Email

If you can't use GitHub's flow, email **jackmmusick@gmail.com** with:

- A description of the issue and its impact
- Reproduction steps
- The affected commit / branch
- Your contact info for follow-up

### Response SLA

- **Acknowledgment:** within 48 hours of report
- **Triage + severity assessment:** within 7 days
- **Patch + advisory disclosure:** depends on severity; we'll communicate
  expected timelines after triage

We don't currently run a paid bug bounty. If your report leads to a fix,
we'll credit you in the advisory and the release notes (unless you'd
rather stay anonymous).

## Supply-Chain Practices

The repo runs:

- **Dependabot alerts + security updates** for `pip`, `npm`, `docker`,
  `github-actions` (see `.github/dependabot.yml`)
- **CodeQL** SAST on push, PR, and weekly schedule
  (see `.github/workflows/codeql.yml`)
- **Secret scanning + push protection** at the repo level
- **OpenSSF Scorecard** weekly, results published to
  https://api.securityscorecards.dev/projects/github.com/gobifrost/bifrost

### Auto-Merge Policy for Dependency Updates

To keep patch SLAs short, Dependabot PRs auto-merge under these conditions:

| Update type | Auto-merge |
|---|---|
| Security advisory bumps | Yes if CI green |
| Patch (`x.y.Z`) | Yes if CI green |
| Minor (`x.Y.z`) | Yes if CI green |
| Major (`X.y.z`) | No — human review |
| Docker base image | No — human review |
| GitHub Actions (pinned to SHA) | Yes if CI green |

Auto-merged PRs still go through the full CI suite (lint, typecheck,
unit, e2e). If a green-CI auto-merge later breaks something, the
behavior is by definition uncovered by tests — the response is to add
the test and fix forward, not to gate the auto-merge harder.

### GitHub App advisory lookup permission

The `bifrost-lockfile-bot` GitHub App reads open Dependabot alerts before
auto-merging security advisory updates. An App owner must set its repository
**Dependabot alerts** permission to **Read-only** at
https://github.com/organizations/gobifrost/settings/apps/bifrost-lockfile-bot/permissions.
GitHub then requires a `gobifrost` organization owner to approve that additional
permission for the existing installation. The workflow treats an open alert on
the same Dependabot package and changed manifest as an advisory association; CI
and closure of the alert after merge remain the evidence that the bump is safe
and effective. Until approval is complete, the workflow fails before it makes
an eligibility decision.

## What's Out of Scope

- Issues in dependencies — report those upstream.
- Issues in self-hosted deployments where the operator misconfigured
  the deployment (open ports, weak passwords, etc.) — these are
  operator concerns, not Bifrost vulnerabilities.
- DoS via deliberate resource exhaustion of a single-tenant deploy.
