# Validation

> Prove the MCP result with observed runs, run the checklist for the mode, and close the report only when it matches the files on disk.

## 1. Inspector Runs

The MCP Inspector CLI runs one method per process and exits with a documented code. Its default protocol era is `legacy`, so always pin the era with `--protocol-era` (`legacy`, `auto`, or `modern`).

```bash
# stdio server built from this repository: the server command is positional
npx @modelcontextprotocol/inspector --cli node build/index.js --protocol-era modern --method tools/list
npx @modelcontextprotocol/inspector --cli node build/index.js --protocol-era modern --method tools/list --strict

# Streamable HTTP server on loopback
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:<port>/mcp --transport http --protocol-era modern --method tools/list

# one read-only tool call
npx @modelcontextprotocol/inspector --cli <server> --protocol-era modern --method tools/call --tool-name <read_only_tool> --tool-arg <key>=<value>

# dual-era target: repeat the list call with --protocol-era legacy
```

Replace `node build/index.js` with the target's own start command. Confirm flag names against the installed Inspector's `--help` before relying on them (`references/build-test-ship.md` records the documented exit codes). Add `--stored-auth-only` in any non-interactive run so the Inspector never starts an OAuth flow, and `--format json` when another step parses the output.

| Exit code | Meaning for the run |
|---|---|
| 0 | Passed |
| 3 | Authorization required: stop and ask; do not log in for the user |
| 4 | Unreachable: the server did not start or listens elsewhere |
| 5 | Tool error or tool not found |
| 6 | `--strict` found a tool-schema portability error |
| other non-zero | Read the one-line JSON error on `stderr` and record it |

When the Inspector cannot run (no Node.js 22.19+, no network for `npx`, or a server that needs a credential), record `not run` with the reason and fall back to the project's own tests and a static review against `rules/mcp-rules.md`. A static review never upgrades a check to `passed`.

## 2. Checks by Mode

| Mode | Required checks |
|---|---|
| build | Project build and tests pass; Inspector list call passes in every claimed era; `--strict` passes; one read-only tool call returns the expected shape; one invalid-input call returns `isError: true`; security checklist (§3) for the deployment shape |
| audit | Every rule in `rules/mcp-rules.md` is marked `pass`, a finding, or `not applicable`, with evidence; read-only runtime checks that need no credential |
| fix | The audit checks, then each fixed finding re-checked by the observation its rule names; no previously passing check fails |
| migrate | Every migration checklist item recorded; no legacy marker left outside a deliberate dual-era layer; Inspector passes in each claimed era; project tests pass |
| connect | Configuration parses; no literal secret in any file; the host lists the server's tools; approvals and allowlists match the task |
| publish | `server.json` validates against the schema it declares; the ownership marker exists; the version is new; the publish command ran only on explicit request |

## 3. Security Checklist

- [ ] No literal credential in source, configuration, URLs, logs, or the report (MCP-S-5).
- [ ] stdio server: credentials come from the environment; `stdout` carries only MCP messages (MCP-P-5).
- [ ] Local HTTP: `Origin` validated, loopback bound, authentication required (MCP-S-4).
- [ ] Remote: the authorization profile is complete and every request's token audience is checked (MCP-S-2, MCP-S-3).
- [ ] Handles and `requestState` are random, expiring, user-bound, and integrity-protected where they matter (MCP-S-7, MCP-P-4).
- [ ] Every tool description was read and carries no unrelated instruction (MCP-D-8).
- [ ] Connect mode: third-party servers pinned and isolated, approvals on for writes and external communication (MCP-S-1, MCP-U-3).

## 4. Report Gate

Before closing the run:

- [ ] `.hyper/mcp/<slug>/report.md` exists and every changed file in the `변경` table exists with that change.
- [ ] Every check row says `passed`, `failed`, or `not run`, and each `passed` row names the command that produced it.
- [ ] Every critical and high finding in scope is closed or listed in `남은 위험` with its blocker.
- [ ] The repair loop stayed within two passes; reverted repairs are recorded.
- [ ] No gated action in `rules/mcp-workflow.md` §4 ran without the user's explicit request.

## 5. Package Changes

When this package itself changes, run the repository's focused skill validator on `skills/hyper-mcp` with `assets/evals/hyper-mcp-cases.jsonl`, the repository verification gate, and an English/Korean structural parity check of every changed file.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Inspector clients, the `legacy` default era, the one-method CLI, exit codes, and `--stored-auth-only` | `references/build-test-ship.md` |
| The security checks | `references/security-and-authorization.md`, `rules/mcp-rules.md` |
| Checks per mode and the report gate | this package's chosen design, not a validated optimum |
