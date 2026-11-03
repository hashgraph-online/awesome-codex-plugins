# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |

## Security Architecture and Boundaries

Ponder is designed with a minimal, auditable attack surface:

- **Zero Runtime Dependencies:** Ponder uses only Node.js built-in modules (`node:fs`, `node:path`, `node:child_process`, `node:crypto`, `node:os`, `node:url`). This invariant is enforced on every commit by `./test/conformance.sh -f deps`.
- **Read-Only on Reviewed Source Code:** Neither `ponder` nor `ponder apply` ever modifies, patches, or deletes target project source files. All session files (`session.json`, `units.json`, `findings.json`, `ledger.jsonl`, and per-pass deliberations/deltas) are written strictly inside `.ponder/<session-slug>/` (or `~/.ponder/sessions/<slug>/`) and any explicit `--out` report path.
- **No External Network or Telemetry:** Ponder makes zero HTTP/HTTPS requests and collects no telemetry. Setting `PONDER_OCA=off` disables the optional local Postgres cognitive bridge (`postgres://localhost/oneiro`).
- **Safe Subprocess Execution:** Subprocesses (`git` for `--diff`/`--strict-scope` and `psql` when `PONDER_OCA` is enabled) are invoked exclusively via `execFileSync` / `spawnSync` with argument arrays (`shell: false`), preventing shell injection.
- **Append-Only Ledger Reconciliation:** `ponder verify` replays `ledger.jsonl` from line 1 and rejects any session where `units.json` or `findings.json` diverges from the append-only ledger (`SPEC.md` Section 3.6).

## Reporting a Vulnerability

If you discover a security vulnerability in Ponder, please report it privately via [GitHub Security Advisories](https://github.com/Quinnod345/ponder/security/advisories/new) rather than opening a public issue.

Please include:
1. The commit SHA or version of Ponder tested.
2. Minimal reproduction steps or proof-of-concept input.
3. The expected behavior versus the observed behavior.

We acknowledge vulnerability reports within 48 hours and aim to ship a verified fix and conformance regression test within 7 days.
