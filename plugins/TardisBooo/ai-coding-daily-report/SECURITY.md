# Security Policy

## Supported versions

Only the latest `main` and the most recent release tag receive security fixes.

## Reporting a vulnerability

Please use [GitHub security advisories](https://github.com/TardisBooo/ai-coding-daily-report/security/advisories/new)
("Report a vulnerability"). Do not open public issues for security problems.

Include: affected version, OS, steps to reproduce, and impact. You will get an acknowledgment
within 72 hours.

## Scope notes

- harness-daily reads session logs **locally** and never uploads them. The only outbound call is
  to the user's own writer CLI (Grok, Claude, or Codex), which receives a per-project prompt
  digest (not full transcripts).
- Reports may contain sensitive paths or prompt text; users are responsible for where they
  store/publish generated reports.
