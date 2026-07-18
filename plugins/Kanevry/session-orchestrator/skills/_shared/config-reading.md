# Session Config Reading

## Resolving the Plugin Root

`$CLAUDE_PLUGIN_ROOT` (Claude Code), `$CODEX_PLUGIN_ROOT` (Codex CLI), `$CURSOR_RULES_DIR` (Cursor IDE), or `$PI_PLUGIN_ROOT` (Pi) may not be set (depends on how hooks/skills are loaded). Resolve the script path with this fallback chain:

1. If `$CLAUDE_PLUGIN_ROOT`, `$CODEX_PLUGIN_ROOT`, `$CURSOR_RULES_DIR`, or `$PI_PLUGIN_ROOT` is set and non-empty, use it.
2. Otherwise, search for the plugin install location (includes Claude Code, Codex, Cursor, and Pi paths):
   ```bash
   PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-${CURSOR_RULES_DIR:-${PI_PLUGIN_ROOT:-}}}}"
   if [[ -z "$PLUGIN_ROOT" ]]; then
     # Check common install locations (Claude Code + Codex CLI + Cursor IDE + Pi)
     for candidate in \
       "$HOME/Projects/session-orchestrator" \
       "$HOME/.claude/plugins/session-orchestrator" \
       "$HOME/.codex/plugins/session-orchestrator" \
       "$HOME/.pi/agent/packages/session-orchestrator" \
       "$HOME/plugins/session-orchestrator" \
       "$HOME/.cursor/plugins/session-orchestrator" \
       "$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}" 2>/dev/null || echo "")")")" \
     ; do
       if [[ -n "$candidate" && -f "$candidate/scripts/parse-config.mjs" ]]; then
         PLUGIN_ROOT="$candidate"
         break
       fi
     done
   fi
   ```

## Parsing Config

> **Canonical Field Reference:** For the complete list of all Session Config fields, types, defaults, and descriptions, see `docs/session-config-reference.md`. Skills should NOT maintain inline copies of field documentation — always reference the canonical doc.

Run `node "$PLUGIN_ROOT/scripts/parse-config.mjs"` to get the validated config JSON. If it exits with code 1, read stderr for the error and report to the user.

Store the JSON output as `$CONFIG` for use throughout this skill — extract fields with `echo "$CONFIG" | jq -r '.field-name'`.

### Handling `agents-per-wave` Overrides

`agents-per-wave` may be a plain integer (`6`) or a JSON object with session-type overrides (`{"default": 6, "deep": 18}`). To get the effective value for the current session type:

```bash
# Plain integer → use directly. Object → check for session-type override, fall back to .default
APW=$(echo "$CONFIG" | jq -r '."agents-per-wave"')
if echo "$APW" | jq -e 'type == "object"' > /dev/null 2>&1; then
  EFFECTIVE_APW=$(echo "$APW" | jq -r --arg st "$SESSION_TYPE" '.[$st] // .default')
else
  EFFECTIVE_APW="$APW"
fi
```

## Handling `agent-mapping` Config

`agent-mapping` is an optional JSON object that maps role keys to agent names. If present, session-plan uses these explicit mappings to assign agents to tasks (overriding auto-discovery matching).

**Role keys**: `impl`, `test`, `db`, `ui`, `security`, `compliance`, `docs`, `perf`

```bash
# Extract agent-mapping (returns null if not configured)
AGENT_MAPPING=$(echo "$CONFIG" | jq -r '."agent-mapping" // empty')
```

Example config in the project instruction file:
```yaml
agent-mapping: { impl: code-editor, test: test-specialist, db: database-architect, ui: ui-designer, security: security-auditor, compliance: austrian-compliance }
```

When `agent-mapping` is not present, session-plan falls back to auto-discovery (scanning the platform's agents directory (`<state-dir>/agents/`) and matching task descriptions against agent descriptions).

## Fallback

If the script is not available (missing file, `$PLUGIN_ROOT` unresolvable), fall back to reading the project instruction file manually per `docs/session-config-reference.md`. The `## Session Config` block is read from `CLAUDE.md` (Claude Code, Cursor IDE) or `AGENTS.md` (Codex CLI, Pi), depending on which platform is active.

## Host-Local Path Resolution (#653)

A small set of path-valued Session Config keys are resolved **host-locally** rather than read straight from the committed `## Session Config` block. This keeps personal/machine-specific paths out of the public repo and lets the same checked-in config run unchanged across machines with different vault roots. Implementation: `scripts/lib/config/host-paths.mjs` (`loadHostPaths()`, `resolveHostPath(key, committedDefault, ctx)`), called from `config.mjs`.

### Which keys resolve host-locally

- **`vault-dir`** — applied to both `config['vault-integration']['vault-dir']` and `config['vault-sync']['vault-dir']`.
- **`plan-baseline-path`** — applied to `config['plan-baseline-path']`.

The values exposed on `$CONFIG` for these keys already reflect the resolved (host-local) result, so downstream skills read them normally without doing their own resolution.

### Precedence chain (highest first)

1. **Environment variable** — `SO_VAULT_DIR` (for `vault-dir`) / `SO_BASELINE_PATH` (for `plan-baseline-path`).
2. **`owner.yaml` `baselines:` per-context match** (`plan-baseline-path` only, #819) — first-match-wins directory-prefix match of cwd against each entry's `match.path-prefix`; resolver: `scripts/lib/named-baseline-resolver.mjs`. Example entry:
   ```yaml
   baselines:
     - name: world-a-baseline
       path: ~/Projects/world-a/projects-baseline
       match: { path-prefix: ~/Projects/world-a }
   ```
3. **`owner.yaml` `paths:` section** — `~/.config/session-orchestrator/owner.yaml` → `paths.vault-dir` / `paths.baseline-path` (see `.claude/rules/owner-persona.md`).
4. **Committed Session Config default** — the value in the `## Session Config` block of `CLAUDE.md` / `AGENTS.md`.

`vault-dir` only ever uses tiers 1, 3, 4 (no per-context match tier); a host without a `baselines:` array resolves `plan-baseline-path` identically to the pre-#819 3-tier chain.

### Empty-tier-falls-through

An empty or whitespace-only value at any tier is treated as unset and falls through to the next tier down. When **all** tiers are unset, the resolved value is `null`/`undefined` — there is no error. In that state `vault-integration` silently degrades to off (the absent path is treated as "no vault configured"), so a host that never sets a vault path simply runs without vault integration.

### Why

- **Privacy-clean:** no personal home path (e.g. a vault root under the operator's home directory) is ever committed to the public repo.
- **Machine-independent / multi-machine portability:** each host can point `vault-dir` / `plan-baseline-path` at its own root via env-var or `owner.yaml` without editing — and re-committing — the shared `## Session Config` block.

## Learning Expiry Semantics

Learnings live exclusively in `.orchestrator/metrics/learnings.jsonl`. The pre-`2.0.0` location `<state-dir>/metrics/learnings.jsonl` is no longer read; consumers with leftover entries should run `scripts/migrate-legacy-learnings.sh` once.

The learning lifecycle states are:

- **Created**: `confidence: 0.5`, `expires_at`: current date + `learning-expiry-days` (default: 30)
- **Confirmed** (same type+subject seen again): `confidence += 0.15` (cap 1.0), `expires_at` reset
- **Contradicted** (evidence against): `confidence -= 0.2` — do NOT reset `expires_at` (let the learning decay naturally if contradicted)
- **Decayed** (untouched this session): `confidence -= learning-decay-rate` (from Session Config, default `0.05`). Applied at session-end after touched-set update, before prune. Clamped to 0.0. Does NOT reset `expires_at`.
- **Expired**: `expires_at < current date` — removed on next write
- **Dead**: `confidence <= 0.0` — removed on next write

**Expiration check semantics:** Compare `expires_at` by date portion only (ignore time-of-day) to avoid intra-day jitter. When writing `expires_at`, set it to `<current_date>T00:00:00Z + learning-expiry-days` (midnight UTC).

**Confidence bounds enforcement:** After EVERY increment or decrement, clamp confidence to [0.0, 1.0]. A learning at 0.95 confirmed becomes 1.0 (not 1.10). A learning at 0.1 contradicted becomes 0.0 and is pruned.

Cleanup (pruning expired + deduplicating by type+subject) runs on EVERY write to `learnings.jsonl`, in both session-end and evolve skills.

## Rule Loading (Glob-Scoped)

Rule files at `.claude/rules/*.md` may carry an optional `globs:` YAML frontmatter field — an array of glob patterns relative to the repo root. The wave-executor calls `loadApplicableRules()` from `scripts/lib/rule-loader.mjs` before each wave to determine which rules apply.

### Glob-Scoped Rule Injection (#336/#694)

**Now wired (was dormant).** The `loadApplicableRules()` loader was implemented + tested under #336 but not actually called in the per-wave prompt path. As of #694 (Epic #693 FA1) it is genuinely wired into the wave-executor via the thin CLI `scripts/print-applicable-rules.mjs`, which the coordinator runs once per wave to produce the injectable `<APPLICABLE-RULES>` block (see `skills/wave-executor/wave-loop.md` § "Pre-Dispatch: Glob-Scoped Rule Injection (#336/#694)"). Authoring guide for the frontmatter keys below: [`docs/rule-authoring.md`](../../docs/rule-authoring.md).

**Frontmatter parsing.** At load time, `rule-loader.mjs` reads the YAML frontmatter block (delimited by `---`) from each `.md` file in `.claude/rules/`. The `globs:` key is expected to be a YAML sequence of glob-pattern strings (e.g. `- src/**/*.tsx`). Flow-style arrays (`globs: ["src/**", "tests/**"]`) are also accepted. Beyond `globs:`, the parser also captures these optional scalar activation keys (#694), each surfaced on the returned `RuleEntry`: `description`, `mode`, `host-class` (→ `hostClass`), `alwaysApply` (boolean; DISTINCT from the `alwaysOn` "no globs" flag), `expires-at` (→ `expiresAt`, ISO date), `learning-key` (→ `learningKey`), `auto-generated` (→ `autoGenerated`, boolean), and `confidence` (number). Unknown keys are ignored without error. Any parse error falls back to always-on (see Failure mode below).

**Match algorithm.** Before each wave begins, the wave-executor reads `allowedPaths` from `wave-scope.json`. This array is passed to `loadApplicableRules()` as `scopePaths`. Glob matching uses **picomatch** (resolved from `node_modules`), with an inline glob-to-RegExp fallback when picomatch is absent — NOT minimatch. For each rule file:

1. If `globs:` is **absent** → rule is always-on; include it unconditionally (subject to the deterministic gates below).
2. If `globs:` is **present and non-empty** → test each `scopePath` against each glob pattern with picomatch (`{ dot: true }`). If at least one `scopePath` matches at least one glob → include the rule. If the intersection is empty → skip the rule for this wave.
3. If `globs:` is **present but empty (`[]`)** → rule matches nothing; never loaded. Reserved for temporarily disabling a scoped rule without removing the file.

**Deterministic gates (#694).** After a successful frontmatter parse, three gates are applied to BOTH always-on and glob-matched candidate rules — a rule must pass ALL active gates to be included:

- **Expiry** — a rule whose parseable `expires-at` is strictly before `now` is EXCLUDED (with a stderr WARN). A malformed `expires-at` never excludes (fail-open).
- **Mode-gating** — when the `mode` param is non-null and the rule declares a differing `mode`, the rule is EXCLUDED. A null `mode` param disables mode filtering; a rule without a `mode` key always passes.
- **Host-class-gating** — symmetric to mode-gating against the `hostClass` param vs the rule's `host-class` value.

Parse-error rules carry no meta, so they pass every gate (fail-open: never silently dropped).

**Call shape.** `loadApplicableRules({ rulesDir, scopePaths = [], mode = null, hostClass = null, now = Date.now() })`. The `mode` / `hostClass` / `now` params are strictly optional and default to "no gating", so the original #336 two-key call shape stays 100% backward-compatible. In the wired path, `scripts/print-applicable-rules.mjs` resolves `scopePaths` from `wave-scope.json` `allowedPaths`, `mode` from `session-type:` in `.claude/STATE.md`, and `hostClass` from `.orchestrator/host.json` (`readHostClass`) — each overridable via a CLI flag and each degrading to `null`/`[]` when unreadable.

**Where in the config-reading flow this hook fires.** After `parse-config.mjs` completes and `$CONFIG` is populated (Phase 2 of session-start / wave-executor pre-wave setup), and after `wave-scope.json` is written, but before the agent prompt for the wave is assembled. The CLI is invoked at the wave boundary so that each wave gets a fresh rule set scoped to its `allowedPaths`. It does NOT run at session-start for the coordinator prompt; the coordinator always receives all always-on rules regardless of scope.

**Token reduction.** Scope-targeted waves that touch only frontend or only Swift files skip unrelated backend, security-web, and other path-scoped rules — typically reducing injected rule content by 30–50% on narrow waves (token reduction target ≥20%, issue #336 acceptance criterion 4).

### Frontmatter format

```yaml
---
globs:
  - src/app/api/**
  - src/routes/**
---
```

Flow-style arrays are also accepted: `globs: ["src/**", "tests/**"]`.

### Loading semantics

- **`globs:` absent** — rule is always-on; loaded for every wave regardless of scope.
- **`globs:` present** — rule loads only when `scopePaths` (the wave's `allowedPaths` from `wave-scope.json`) intersects at least one glob pattern.
- **`globs: []` (empty array)** — rule matches nothing; never loaded. Reserve for temporarily disabling a scoped rule.

### Wave-executor integration

In the live path the coordinator does NOT call the loader directly — it runs the CLI `scripts/print-applicable-rules.mjs` (which calls the loader) once per wave and captures stdout as the `<APPLICABLE-RULES>` block:

```sh
RULES_BLOCK="$(node "$PLUGIN_ROOT/scripts/print-applicable-rules.mjs" 2>/dev/null)"
# Empty stdout (no .claude/rules/, no matches, or any failure) → inject nothing.
```

The CLI resolves the loader arguments from on-disk state (`wave-scope.json` `allowedPaths`, `STATE.md` `session-type:`, `host.json` `host_class`) and prints either the injectable Markdown block or, with `--json`, `{ count, rules: [{ path, alwaysOn, matchedGlobs }] }`. The underlying loader call it performs is equivalent to:

```js
import { loadApplicableRules } from 'scripts/lib/rule-loader.mjs';

const rules = loadApplicableRules({
  rulesDir: '.claude/rules',          // absolute path
  scopePaths: wave.allowedPaths,      // from wave-scope.json
  mode: sessionType,                  // from STATE.md session-type: (null → no mode gating)
  hostClass,                          // from host.json host_class (null → no gating)
  // now defaults to Date.now() — injectable for tests / deterministic expiry
});
// rules[n].alwaysOn === true  → cross-cutting rule (no globs frontmatter)
// rules[n].alwaysOn === false → scope-matched rule
// rules[n].matchedGlobs       → which patterns triggered inclusion
```

### Backward compatibility

- Rule files without any frontmatter continue to load as always-on. No migration required.
- Files already using the old `paths:` frontmatter key do not match `globs:` — they are treated as always-on until updated.

### Failure mode

Frontmatter parse errors write a warning to stderr and fall back to always-on. A rule is **never silently dropped** — degraded loading is always preferable to missing a security or architecture constraint.
