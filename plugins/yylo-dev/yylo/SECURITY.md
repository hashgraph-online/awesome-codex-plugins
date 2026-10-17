# Security Policy

## Supported versions

Security fixes land on `main` and ship in the next `@yylo/cli` npm release.
Older minor lines are supported on a best-effort basis.

## Reporting a vulnerability

Please report vulnerabilities privately:

- open a GitHub security advisory at
  https://github.com/yylo-dev/yylo/security/advisories/new, or
- email the maintainers listed in `package.json`.

Do **not** open a public issue for suspected vulnerabilities. We aim to
acknowledge reports within 72 hours.

## Scope

- The `yylo` CLI, its bundled templates (`src/templates/**`), and the
  task/merge orchestration scripts they generate.
- The controller repositories `yylo-dev/yylo-skills`, `yylo-dev/yylo-benchmark`,
  and `yylo-dev/yylo-ledger` for issues in their own code.

### Out of scope

- Vulnerabilities in the AI coding agents (`pi`, Claude Code, Codex, Gemini
  CLI, ...) that yylo orchestrates — report those upstream.
- Secrets intentionally committed as obviously-dummy test fixtures
  (obviously-fake Slack/GitHub fixture tokens and similar
  placeholders). See `docs/security-scanner-baseline.md` for the audited list.

## Automation security posture

- yylo drives third-party coding agents inside per-task git worktrees; the
  merge queue — not interactive approval inside a worktree — is the safety
  boundary for repository changes.
- Shell execution is centralized in bounded runners (array-form `spawnSync`,
  command files, wall-clock budgets). See
  `docs/security-scanner-baseline.md` for the rule-by-rule audit.
- Continuous scanning: `.github/workflows/hol-plugin-scanner.yml` runs the
  [HOL Plugin Scanner](https://github.com/hashgraph-online/hol-guard) on every
  push and pull request.
