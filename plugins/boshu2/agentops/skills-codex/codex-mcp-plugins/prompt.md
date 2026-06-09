# Codex Execution Profile — codex-mcp-plugins

Read the sibling base skill `../SKILL.md` (full overview, constraints, output
spec, rubric, examples, troubleshooting) before acting. This profile is the
Codex-native, step-ordered execution path; the base SKILL.md is the source of truth.

## Steps

1. **Confirm the live surface.** Run `codex mcp --help` and `codex plugin --help`
   (and `codex plugin marketplace --help`). The subcommand shape changes between
   releases — never act on a remembered shape.
2. **Inventory.** Run `codex mcp list --json`, `codex plugin marketplace list`,
   and `codex plugin list --json`. Record what already exists.
3. **Decide the path.** Tool-reach (an MCP server) → step 4. Bundle distribution
   (a plugin marketplace) → step 5.
4. **Wire an MCP server.** Choose stdio XOR HTTP — never mix:
   - stdio: `codex mcp add <NAME> [--env KEY=$VAR] -- <command> [args...]`
   - HTTP: `codex mcp add <NAME> --url <URL> --bearer-token-env-var <ENV_VAR> [--oauth-client-id ... --oauth-resource ...]`
   Then `codex mcp get <NAME> --json` to confirm the written entry. For an
   OAuth-protected server, `codex mcp login <NAME>` (add `--scopes a,b,c` if scoped).
5. **Ship a plugin bundle.** Register the marketplace snapshot first, then install:
   `codex plugin marketplace add <SOURCE>` → `codex plugin list --available --json`
   → `codex plugin add <PLUGIN>@<MARKETPLACE>` (or `-m <MARKETPLACE>`). Refresh a
   Git marketplace with `codex plugin marketplace upgrade [<name>]`.
6. **Verify end-to-end.** Run a real `codex exec` worker that calls an MCP tool or
   uses a bundled skill. Config is not "wired" until a worker actually uses it.
7. **Capture artifacts.** Save `codex mcp list --json` / `codex plugin list --json`
   output into the session/handoff as the verification surface.

## Guardrails

- **Verify before acting.** No remembered subcommand shapes — `--help` first (step 1).
- **stdio vs HTTP is mutually exclusive.** `--env` and a bare command are stdio-only;
  `--bearer-token-env-var` is HTTP-only. A mixed `add` is rejected and a half-written
  entry breaks every later `codex` run.
- **Never inline secrets.** Pass tokens by env-var reference (`--env KEY=$VAR`,
  `--bearer-token-env-var ENV_VAR`). `config.toml` is plaintext and often synced —
  an inlined token leaks across the fleet.
- **Plugins require a marketplace first.** `codex plugin add` resolves against a
  configured marketplace snapshot — `marketplace add` before `plugin add`.
- **Idempotent.** Check `codex mcp get <NAME>` / `codex plugin list` before adding;
  `remove` then `add` to repair, never blind re-add.
- **OAuth is a separate step.** `add` registers; `login` authenticates. A registered
  server is dead until login completes.
- **Binary owns the write.** Let `codex mcp add` / `codex plugin add` edit
  `~/.codex/config.toml` — never hand-edit the MCP/plugin tables.
- **Backstage only.** Never surface these commands or framing in client-facing
  AI Partner content.
