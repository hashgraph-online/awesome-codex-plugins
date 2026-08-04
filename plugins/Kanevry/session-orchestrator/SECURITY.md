# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.x | Yes |
| 2.x and earlier | No |

Only the latest 3.x minor receives fixes. See [CHANGELOG.md](CHANGELOG.md) for the
current release.

## Reporting a Vulnerability

If you discover a security vulnerability in Session Orchestrator, please report it responsibly.

**Email:** [security@gotzendorfer.at](mailto:security@gotzendorfer.at)

Please include:
- Description of the vulnerability
- Steps to reproduce
- Affected files/skills
- Potential impact

**Response time:** We aim to acknowledge reports within 48 hours and provide a fix or mitigation plan within 7 days.

## Scope

Session Orchestrator is a plugin for AI coding agents (Claude Code, Codex CLI,
Cursor, Pi), composed of Markdown instructions plus a Node ESM runtime under
`scripts/` and `hooks/`. It requires Node 24+.

What it **does** touch:

- **Local filesystem** — reads/writes repo files, `.orchestrator/` runtime state,
  and (when vault integration is enabled) a host-local vault directory under `$HOME`.
- **Your VCS CLI** — spawns `glab` / `gh` using your existing authentication.
- **Credentials via environment** — reads `GITLAB_TOKEN` (baseline fetch),
  `CLANK_EVENT_SECRET` (event-bus bearer token), and `NPM_TOKEN` from a gitignored
  `.env.local` (publish flow only). It never persists them; `CLANK_EVENT_SECRET` is
  transmitted as a bearer token when the event bus is configured. See
  [.env.example](.env.example).
- **Outbound network, all opt-in and off by default** — event-bus webhook POSTs
  (only when `CLANK_EVENT_URL` *and* `CLANK_EVENT_SECRET` are set), GitLab API
  baseline fetches (only with `GITLAB_TOKEN`), and anonymous usage telemetry
  (strictly opt-in, one-time consent, whitelist-projected — see
  [docs/telemetry.md](docs/telemetry.md)).
- **An optional self-hosted ingest server** — `server/ingest/` is a small HTTP
  service (with `Dockerfile`, rate limiting, SQLite persistence, retention) that an
  operator may deploy to *receive* telemetry. It is not run by the plugin and is not
  required to use it.

What it does **not** do:
- Execute user-provided code directly
- Store or forward credentials to any third party
- Send anything over the network without an explicit opt-in

Security concerns are most likely to involve:
- **Hook scripts** (`hooks/*.mjs`) — command injection via crafted file paths or tool input
- **Skill instructions** — prompt injection that could bypass scope enforcement or safety constraints
- **Agent dispatch** — unintended tool access or scope escalation during wave execution
- **Session Config** — the `*-command` keys are executed via a shell; see
  [Session Config Command Trust](#session-config-command-trust) below

## Disclosure

We follow [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure). Fixes are committed with a security advisory once a patch is available.

## Enforcement Architecture

Enforcement is a set of `PreToolUse` / `PreToolUse`-adjacent hooks registered via
`hooks/hooks.json` (with per-platform variants for Codex, Cursor, and Pi). All are
Node ESM; the former Bash implementations were removed in the v3.0.0 native
migration (#137/#138).

### Wave-scoped enforcement

Both wave guards read a `wave-scope.json` that the wave-executor writes before
dispatching each wave. Its location is **platform-resolved** by
`scripts/lib/scope-gate.mjs` — `.claude/`, `.codex/`, `.cursor/`, or `.pi/` under
the project root, depending on the host agent.

**File scope (`hooks/enforce-scope.mjs`)** intercepts `Edit`, `Write`, and
`MultiEdit`. It resolves the target through `realpath` (symlink-bypass defense) and
matches the result against `allowedPaths` — prefix, glob, or exact literal. An
explicit *absolute* allowlist entry is honoured before the project-root containment
check (#792), so a deliberate out-of-repo grant is reachable; every other
out-of-repo path is denied.

**Command scope (`hooks/enforce-commands.mjs`)** intercepts `Bash` and matches the
command against `blockedCommands[]` using word-boundary matching (so `rm` does not
match `format`). When `blockedCommands` is empty or absent, a hardcoded fallback
list applies (`rm -rf`, `git push --force` / `-f`, `git reset --hard`,
`drop table`, `git checkout -- .`).

Both hooks **fail closed**: any unhandled internal error emits a deny, never a
silent allow.

### Enforcement levels

Both wave guards read the `enforcement` field from `wave-scope.json`:

| Level | Behavior | Exit code |
|-------|----------|-----------|
| `strict` | Deny the operation via `hookSpecificOutput.permissionDecision: deny` on stdout | 0 |
| `warn` | Allow the operation, emit stderr warning | 0 |
| `off` | Skip all checks | 0 |

A deny exits **0**, not 2 (#906). Per the Claude Code hook contract a hook signals
either by exit code alone or by exit 0 plus structured JSON — never both; under
`exit 2` stdout JSON is discarded, which previously swallowed every deny reason.
The emitter is `scripts/lib/io.mjs#emitDeny`; see its JSDoc for the full payload.

**Default is `strict`** (fail-closed) when the `enforcement` field is missing.

### Dynamic per-wave scoping

Scope constraints change between waves:

- **Discovery waves** use empty `allowedPaths` (deny-all writes) combined with
  explicit read-only agent instructions (dual enforcement — hook-level + prompt-level).
- **Quality waves** use two-phase scope: production file patterns for simplification
  passes, then test-only patterns (`**/*.test.*`, `**/*.spec.*`) for test/review passes.

### Session-level guards (active outside waves)

| Hook | Protects against |
|---|---|
| `pre-bash-destructive-guard.mjs` | Destructive shell commands in the **main** session, per `.orchestrator/policy/blocked-commands.json` (13 rules, `block` or `warn` severity, each citing its source rule). Bypass requires `allow-destructive-ops: true` in Session Config. |
| `config-protection.mjs` | Edits that *loosen* a quality gate — lowered thresholds, added `eslint-disable`/`@ts-ignore`, rules flipped to `off`, widened `.gitleaks.toml` allowlists, relaxed tsconfig strictness. Warn-by-default, fail-open on internal error. |
| `pre-bash-staging-fence.mjs` + `wave-scope-commit-guard.mjs` | Concurrent `git add` races between parallel wave-agents, and lint-staged sweeps that re-stage files outside wave scope. Rejects the commit rather than the edit. |

The behavioural rules these guards mechanise are documented in
[`.claude/rules/parallel-sessions.md`](.claude/rules/parallel-sessions.md) (PSA-003,
PSA-004, PSA-007).

## Supply Chain

- `.npmrc` sets `ignore-scripts=true` — no dependency may run install/postinstall
  scripts. This is the primary defense against postinstall-style attacks (SEC-020).
- CI enforces `npm audit --omit=dev --audit-level=high`.
- **gitleaks** (37 rules) and an **owner-leakage scanner**
  (`scripts/lib/validate/check-owner-leakage.mjs`) both run in CI and as `.husky/`
  pre-commit stages, so a secret or private-path leak is normally blocked before it
  reaches a public branch. Note the asymmetry: the owner-leakage stage is
  unconditional, whereas the local gitleaks stage is **skipped silently when gitleaks
  is not installed** — CI remains the backstop for that one, and `--no-verify`
  bypasses both.
- This repo is **npm-canonical**: `package-lock.json` is the committed lockfile and
  `scripts/check-package-manager.mjs` guards against a foreign lockfile appearing.

## Session Config Command Trust

The Session Config keys `test-command`, `typecheck-command`, `lint-command`, and
`custom-phases[].command` are executed via a shell. A malicious commit to
`CLAUDE.md` could therefore inject commands — which is **RCE-equivalent within the
repo's existing trust model**, not a new attack surface: anyone able to commit can
already achieve the same through `package.json` scripts, `.husky/` hooks, or a test
file.

The mitigation is review, not sandboxing: treat Session Config like code. Any diff
touching a command-bearing key must show before/after. `custom-phases` additionally
rejects shell metacharacters as defense-in-depth. Full trust model in
[`.claude/rules/security.md`](.claude/rules/security.md).

## Prerequisites

- **Node.js 24+.** v3.x is Node ESM throughout; there is no Bash runtime dependency
  for the hooks (`jq` is used only by a few `scripts/` validators, never by
  `hooks/*.mjs`).
- Hooks run inside the host agent's harness as tool-use interceptors, not as
  standalone scripts.

## Known Limitations

1. **No wave enforcement outside active waves** — when no `wave-scope.json` exists
   (between sessions, before the first wave, after cleanup), the two wave guards exit 0.
   The session-level guards in the table above remain active.

2. **Prompt injection via VCS content** — issue titles and descriptions fetched via
   `glab`/`gh` are consumed in agent prompts without sanitization. A malicious issue
   body could inject instructions into an agent's context. Mitigated by: issues are
   typically user-created in controlled workflows, and wave scope enforcement limits
   the blast radius of any injected instructions.

3. **Plugin relies on the host harness** — tool-level enforcement is provided by the
   agent's hook system. The plugin cannot enforce restrictions if hooks are bypassed
   at the harness level (`disableAllHooks`, `--no-verify`, etc.).

4. **Session Config values are only partially validated** — `health-endpoints`,
   `plan-baseline-path`, and `cross-repos` accept arbitrary strings. Do not embed
   credentials in these fields (see Credential Safety below).

5. **Guards are heuristics, not proofs** — `config-protection.mjs` is a
   low-false-positive line/regex heuristic, not an exhaustive AST gate, and fails
   open by design so a guard bug never blocks legitimate work.

## Credential Safety

- Secrets are read from the environment or a gitignored `.env.local`, never written
  into repo files by the plugin.
- VCS CLI tools (`glab`, `gh`) use your existing authentication; their credential
  security is your responsibility.
- **Do not embed API keys, passwords, or auth tokens** in Session Config fields
  (especially `health-endpoints` URLs). Session Config lives in `CLAUDE.md`, which is
  normally committed.
- **Do not paste tokens into permission allowlists** in `.claude/settings.json` or
  `.claude/settings.local.json` (SEC-021). `settings.local.json` is conventionally
  untracked, so the pre-commit leakage scanner — which enumerates tracked files —
  structurally cannot see a token pasted there.
