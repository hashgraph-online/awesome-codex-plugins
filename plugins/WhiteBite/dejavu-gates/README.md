> [!IMPORTANT]
> **[`opencode-dejavu`](https://github.com/WhiteBite/opencode-dejavu) has been RENAMED to [`dejavu-gates`](https://github.com/WhiteBite/dejavu-gates) — you are on the new home.**
> The old URL [github.com/WhiteBite/opencode-dejavu](https://github.com/WhiteBite/opencode-dejavu) redirects here permanently.
> - **OpenCode config:** `{ "plugin": ["opencode-dejavu"] }` → `{ "plugin": ["dejavu-gates"] }`
> - **git remote:** `git remote set-url origin https://github.com/WhiteBite/dejavu-gates.git`
> - **npm:** the old package [`opencode-dejavu`](https://www.npmjs.com/package/opencode-dejavu) is deprecated and frozen at 2.27.0; all releases from 2.39.0 are [`dejavu-gates`](https://www.npmjs.com/package/dejavu-gates)

<p align="center">
  <img src="logo/icon.svg" width="96" height="96" alt="dejavu logo — a lowercase d with two amber echo strokes">
</p>

<h1 align="center">dejavu — error gates for AI coding agents</h1>

<p align="center"><b>English</b> | <a href="README.ru.md">Русский</a></p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/harnesses-10-green.svg" alt="OpenCode, Claude Code, Codex, Gemini CLI, Cursor, Copilot CLI, Crush, Devin CLI, Kiro, Cline">
  <img src="https://img.shields.io/badge/TypeScript-Bun-black.svg" alt="TypeScript + Bun">
  <img src="https://github.com/WhiteBite/dejavu-gates/actions/workflows/ci.yml/badge.svg" alt="CI">
</p>

![dejavu-gates demo: the same failing deploy call is counted across sessions, promoted to a blocking gate, teaches the agent with CORRECTION and EVIDENCE, blocks a same-session repeat, then heals after three successes](assets/dejavu-gates.gif)

Agents repeat the same mistakes because they forget between sessions — and markdown rules don't fix that. dejavu is a cross-session **memory prosthesis with teeth**: it mechanically detects recurring tool-call failures (bash, read, edit, write, glob, grep), promotes them into enforced gates, teaches the agent with a reminder, blocks a same-session repeat offense — and retires the gate when the command starts succeeding again. One engine, many hosts: OpenCode (plugin), Claude Code, Codex CLI, Gemini CLI, Cursor, Copilot CLI, Crush, Devin CLI, Kiro (hook-handler CLI), Cline (in-package plugin). TypeScript + Bun, ships as source, no build step.

Deep mechanics live in [docs/reference.md](docs/reference.md) — this README carries the essentials.

## Quickstart

**OpenCode** (installs automatically at startup; V1 uses the `plugin` key, V2 renamed it to `plugins`):

```jsonc
// ~/.config/opencode/opencode.json (global) or opencode.json (project)
{ "plugin": ["dejavu-gates"] }   // OpenCode V1    — or { "plugins": ["dejavu-gates"] } on V2
```

**Any other harness** — one command, auto-detects installed harnesses, project scope:

```bash
npx -y dejavu-gates install      # add --user for user scope; npx -y dejavu-gates hooks --check to verify
```

Nothing to configure. Gates appear automatically as failures recur — the first reminder fires after the third failure of the same pattern across two sessions.

Optional, later: [tune what the agent is told](#observability) (`dejavu lesson`), [read the store](#data-files), or enable the opt-in [recovery channels](#recovery-channels-opencode-opt-in).

## How it works

```
tool call fails  →  signature normalized (paths/numbers/hashes stripped)
                  →  pattern-key counted, sessions tracked
                  →  3 failures across 2 distinct sessions  →  gate promoted
  next attempt     →  [dejavu] REMINDER (call aborted, agent sees the correction)
  retry fails again →  same-session repeat offense → hard BLOCK on further attempts
  diagnostic cmd   →  gate stays remind-only: the call RUNS and the reminder rides
                      on the failing output as a [dejavu] NOTE (once per session)

the loop closes on behavior, in both directions:
  fixed command keeps succeeding  →  3 successes → gate HEALS → retires (watching)
  agent keeps fighting the gate   →  recurrences / dejavu:proceed overrides → DEMOTES
  60 days without recurrence      →  gate EXPIRES
```

Design decisions (post-mortem of existing approaches):

- **Remind first, block on repeat.** Pure blocking starts an arms race — the agent routes around gates (`npm` blocked → uses `pnpm`). A reminder with the correction teaches; the block is reserved for ignored reminders.
- **Gate messages are teachers.** Every message carries `CORRECTION:` (what to do instead) and `EVIDENCE:` (N failures across M sessions), not just a prohibition.
- **Mechanical pattern-keys only.** No LLM-based error classification in the hot path — the unreliable component doesn't do reliability work.
- **Two scopes.** Repo-specific gotchas live in `<repo>/.opencode/dejavu/` (committable); patterns seen in 2+ project dirs are agent-level habits and move to `~/.config/opencode/dejavu/`. A global pattern index (`index.json`) counts distinct project dirs per key and drives the escalation.
- **Enforcement has negative feedback.** A gate the agent keeps fighting demotes itself and never re-promotes mechanically; a single stubborn session cannot disarm a gate (both votes need distinct sessions). A human can always re-enforce — see [gates.json](#what-a-gate-looks-like).
- **No identity, no teeth.** A signature whose substance was entirely parameterized away (`cmd <path> <str>`, `node <str>`) matches a whole command family and can never enforce — it may only watch.
- **Fail-open, always.** The hook CLI never wedges a host: malformed payloads, a broken store, or an internal dejavu bug produce `{}` + exit 0. stdout carries only the decision JSON; everything else goes to stderr.

## What a gate looks like

`gates.json` is plain, human-editable JSON — delete an object to disable the gate, edit `correction` to teach something better:

```jsonc
// <repo>/.opencode/dejavu/gates.json
{
  "key": "bash:deploy-to-staging88f",        // pattern key — the gate's identity
  "signature": "bash:deploy --to <path> --env <str>",  // normalized call shape
  "tool": "bash",
  "status": "blocking",                      // blocking | reminding | watching
  "count": 4,                                // lifetime failures
  "sessions": ["s1", "s2"],                  // distinct sessions that failed
  "snippet": "Error: unknown flag --env",     // captured evidence (secret-scrubbed)
  "correction": "Last error: \"unknown flag --env\" — use --environment instead.",
  "recurredAfterGate": 0,                    // THE health metric: did the error survive the reminder?
  "firstSeen": "2026-08-21T10:00:00.000Z",
  "lastSeen": "2026-09-29T18:12:00.000Z"
}
```

## Use cases

- **A command that keeps failing across sessions.** After 3 failures across 2 distinct sessions a gate promotes; the next attempt is aborted with a `CORRECTION:` reminder, and a same-session retry after a failed reminder blocks.
- **Failing diagnostics that must keep running.** `tsc`, `pytest`, `cargo test` and other diagnostics promote to `reminding` — the call runs, a `[dejavu] NOTE` rides the failing output once per session, nothing is interrupted.
- **Repeated file-probe failures.** Reads of missing files and rejected edits land in `watching` gates — measured and reportable, never interrupting.
- **Foreground servers that strand orphans.** `npm run dev`, `uvicorn`, `next dev` starts are interrupted in the before-hook with a run-detached correction (tmux / `nohup … &`).
- **One habit, every harness.** Signatures normalize before hashing, so the same failing call is gated in whichever host shares the store — a gate learned in Claude Code fires in OpenCode, Cursor, or anywhere else.
- **Curating what the agent is told.** `dejavu lesson list` surfaces gates still on machine-default corrections; `lesson set` replaces them with a human fix.

## Why choose this

- **Learning and enforcement in one loop.** A Sep 2026 survey of ~60 OSS projects found no shipped tool that both learns rules from observed failures and blocks tool calls — policy engines never learn, memory plugins never block ([details and caveats](#comparison-with-analogs)).
- **A mechanical hot path.** Pattern-key counting and Levenshtein ≤ 0.3 fuzzy merging decide every promotion — no LLM in the failure path.
- **Gates answer to behavior.** 3 post-gate recurrences or 3 explicit overrides demote a gate; 3 consecutive successes heal it; 60 days without recurrence expires it.
- **One store, 10 harnesses.** OpenCode, Claude Code, Codex CLI, Gemini CLI, Cursor, Copilot CLI, Crush, Devin CLI, Kiro, and Cline read and write the same gates.

## Who is it for

- **Solo agent-heavy developers** — gates accumulate from your own `log.jsonl` evidence, so enforcement matches your actual failure history, not a generic rulebook.
- **Multi-harness users** — one store shared across all supported hosts.
- **Teams that want enforcement without hand-written policy** — gates promote mechanically from recurrence and demote themselves when the agent stops fighting them; humans only edit corrections.

## Supported harnesses

| Harness | Install | Block (pre) | Remind NOTE (post) | Notes |
|---|---|---|---|---|
| **OpenCode** | npm plugin / source | ✅ | ✅ | full integration: all channels, repeat guard, compaction context |
| **Claude Code** | `install-hooks.ts` | ✅ | ✅ | `additionalContext` annotations; `SessionStart` hook injects a gate digest (top enforced gates); hooks carry no exit codes → text detection |
| **Codex CLI** | `install-hooks.ts` | ✅ | ✅ | hooks are stable and on by default; Pre/PostToolUse fire for every tool; a first-run trust prompt may still apply to project hooks |
| **Gemini CLI** | `install-hooks.ts` | ✅ | ✅ | BeforeTool/AfterTool |
| **Cursor** | `install-hooks.ts` | ✅ | ✅ | shell events + CC-compatible events |
| **Copilot CLI** | `install-hooks.ts` | ✅ | ✅ | camelCase + PascalCase payload families |
| **Crush** | `install-hooks.ts` | ✅ | ❌ degraded | upstream has PreToolUse only — enforcement + shared store still protect; no post annotations |
| **Devin CLI** | `install-hooks.ts` | ✅ | ✅ | `.devin/hooks.v1.json` root-event merge; Claude-format hooks also auto-import from `.claude/settings.json` |
| **Kiro** | `install-hooks.ts` | ✅ | ✅ | `.kiro/hooks/dejavu-gates.json`; the NOTE rides raw hook stdout (Kiro's context channel); project scope only |
| **Cline** | `cline plugin install --npm dejavu-gates` | ✅ | ✅ | in-package plugin host (`src/cline-plugin.ts`); SDK/CLI/Kanban only; no exit codes → text detection |
| Zed, Aider | — | ❌ | ❌ | no hook API to intercept tool calls — not portable |
| Windsurf, Amp | — | (planned) | ❌ | block-only / fire-and-forget surfaces; deferred until context injection exists |

**Unified store — gates travel across harnesses.** Every host reads/writes the same store (`<repo>/.opencode/dejavu/` + `~/.config/opencode/dejavu/`, `DEJAVU_HOME` overrides). Call signatures are harness-neutral (tool names and arg fields are normalized before signing), so a gate learned in Claude Code fires in OpenCode, Cursor, or anywhere else — and vice versa.

## Install

Prerequisite for every path: [Bun](https://bun.sh) on PATH (hook handlers run raw TypeScript; no build step).

The installer merges idempotently into each harness's config (foreign hooks and fields survive), backs the file up to `<config>.dejavu-bak` before mutating, refuses to touch unparseable configs, and writes hook commands that call the installed package's CLI directly (never `npx` in the hot path — hooks fire on every tool call). Or install the package once (`npm i -g dejavu-gates` or `npm i -D dejavu-gates`) and use the `dejavu` / `dejavu-gates` command instead of `npx -y`.

<details>
<summary><b>Native plugin channels, GitHub Packages mirror, from-source OpenCode, manual invocation</b></summary>

Native plugin channels (no npx, auto-updating):

| Harness | Command |
|---|---|
| Claude Code | `claude plugin marketplace add WhiteBite/dejavu-gates` then `claude plugin install dejavu-gates@dejavu-marketplace` |
| Codex CLI | `codex plugin add WhiteBite/dejavu-gates` (hooks are enabled by default; approve the first-run trust prompt if it appears) |
| Copilot CLI | `copilot plugin install WhiteBite/dejavu-gates` |
| Cursor | IDE: `/add-plugin` → browse marketplace → dejavu-gates (or copy the repo to `~/.cursor/plugins/local/dejavu-gates`) |
| Gemini CLI | `gemini extensions install https://github.com/WhiteBite/dejavu-gates` |
| Crush / Devin / Kiro / Cline | no plugin marketplace — use the installer above, or `cline plugin install --npm dejavu-gates` for Cline |

The companion reaction protocol (`skills/dejavu/`) ships inside the plugin bundle and is auto-discovered by the Claude Code, Cursor, and Gemini CLI plugin formats.

GitHub Packages (authenticated mirror, `@whitebite/dejavu-gates`) and the `.npmrc` it needs: see [reference — harness installation notes](docs/reference.md#harness-installation-notes).

OpenCode from source:

```bash
git clone https://github.com/WhiteBite/dejavu-gates ~/.config/opencode/vendor/dejavu
cd ~/.config/opencode/vendor/dejavu && bun install
```

```ts
// ~/.config/opencode/plugins/dejavu.ts
export { Dejavu } from "../vendor/dejavu/index.ts"
```

Companion skill (agent behavior protocol): copy `skills/dejavu/` to `~/.config/opencode/skills/dejavu/`.
Status command: copy `commands/dejavu.md` to `~/.config/opencode/command/dejavu.md` (Claude Code, Cursor, and Gemini CLI pick the same command up from the plugin bundle automatically: `commands/dejavu.md` for the first two, `commands/dejavu.toml` for Gemini).

Manual / from a clone (all harnesses):

```bash
git clone https://github.com/WhiteBite/dejavu-gates && cd dejavu-gates && bun install
bun scripts/install-hooks.ts --harness claude            # project scope (cwd)
bun scripts/install-hooks.ts --harness claude --user     # user scope (~/.claude/...)
bun scripts/install-hooks.ts --harness codex --dry-run   # preview without writing
```

</details>

## How it behaves

**Blocking policy.** Only `bash` commands that are NOT diagnostics may ever become blocking gates. Diagnostics and iteration commands (`tsc`, `pytest`, `cargo test`, `go build`, `dart run`…) promote to `reminding` — they annotate the failing output and never block, so iterating on tests/builds is never punished. File probes (read/edit/write/glob/grep) stay `watching`: measured, never interrupting. `canBlock()`/`canRemind()` in `src/patterns.ts` are the single source of truth.

**Proactive guards** — five shape-based interruptions in the before-hook (foreground dev-server starts, spawn patterns that hang the call, orphaned `Start-Job`, command-accretion snowballing). Every one teaches a concrete alternative and is bypassable with `# dejavu:proceed` (logged). Full mechanics: [reference — proactive guards](docs/reference.md#proactive-guards).

**Payload hygiene (OpenCode only)** — a stateless transform-hook pass for the outgoing payload: consecutive identical tool calls get sanitized and a third gets hard-blocked (prevents the DashScope identical-call HTTP 400 that poisons a session), repeated shapes earn an advisory note, a model stuck re-issuing a blocked call gets an automated synthetic user turn that ends the loop. Details: [reference — payload hygiene channels](docs/reference.md#payload-hygiene-channels).

**Data safety** — terminal control characters and secrets are scrubbed before anything touches disk; gate mutations run under an exclusive lockfile with tmp+rename writes; an unparseable `gates.json` is quarantined (bytes preserved) and mechanically repaired on the next init; a transiently-unreadable store throws instead of parsing as empty. Full mechanics: [reference — data safety](docs/reference.md#data-safety).

**Gate lifecycle** — gates heal (3 consecutive successes), retire as taught (5+ reminders, zero reoffense), retire as chronic, demote when the agent fights them, expire after 60 days without recurrence; a promoted-and-retired-thrice oscillation is terminal. Every promoted gate ships with a mechanical default correction chosen by command family — a gate never sits "NOT TEACHING" awaiting a human. Details: [reference — gate lifecycle](docs/reference.md#gate-lifecycle).

### Recovery channels (OpenCode, opt-in)

Two passes for provider-side degeneration, both OFF by default (`1`/`true`/`yes` to enable). No gates, no persistence, no promotion — full mechanics in [reference](docs/reference.md#recovery-channels-opencode-opt-in).

- **Leaked tool-call recovery** (`DEJAVU_LEAK_RECOVERY=1`) — an OpenAI-compatible gateway can intermittently leak tool-call serialization into the assistant message as plain text instead of a structured tool call: the full `<|DSL|calls>…</|DSL|calls>` block, a stream cut inside it, or tool-call tags serialized as text — any `<junk@tool …>…</junk@tool>` / `<junk/tool …>` shape carrying a known tool word, attributes included, so an unknown prefix needs no release. The repeat channel detects every dialect (DSL block tail-anchored; fenced examples, quoted spans and inline mentions are left alone), neutralizes the guard-passing blocks in the outgoing payload so the model never sees its own broken emissions, and appends a synthetic user turn telling the model to re-issue the intended call as a proper tool call.
- **Loop recovery** (`DEJAVU_LOOP_RECOVERY=1`) — a reasoning model stuck in lexical spam or a hedge-heavy deliberation loop never emits a tool call. The host runs the pure `detectStuckReasoning` detector (Unicode-aware, digits excluded so numeric data never fires) over the streaming reasoning, aborts the session and injects a corrective user turn — capped at 2 landed injections per session with a 30s cooldown and a two-checks confirmation before any abort.

## Detection coverage

| Channel | Catches |
|---|---|
| exit code + output text (OpenCode `tool.execute.after`) | bash failures (non-zero exit, TS errors, test failures, stack traces) |
| output text only (external harness post hooks — no exit codes exist there) | failure-shaped output: `error TS…`, `FAIL`, `panic:`, `[ERROR]`, PHPUnit/`FAILURES!`, `Fatal error:`, TAP `not ok`, … |
| `message.part.updated` event scan (OpenCode) | tool-level failures (read of missing file, rejected edits) that never reach the after-hook; error text is Sentry-style parameterized |
| chain-segment matching | gates fire even when the gated command hides inside `x && gated-cmd` chains, `cmd /c "..."` wrappers, or `$(...)` / backtick substitutions |
| `experimental.chat.messages.transform` (OpenCode) | repeat channel: consecutive identical tool calls sanitized in the outgoing payload + NOTE at 2nd round, hard block at 3rd |
| companion skill | agent behavior protocol (how to react, when to annotate) |
| `/dejavu` command | status report: active gates, recurrence metric, review flags |

Language ecosystems covered by failure detection: JS/TS, Python, Go, Rust, Java/Kotlin/Scala (Maven/Gradle/sbt), .NET, Ruby, PHP (PHPUnit), Dart/Flutter, C/C++, Elixir; shells: bash, PowerShell, cmd. Not covered (by design): semantically-equivalent-but-syntactically-different failures beyond fuzzy (Levenshtein ≤ 0.3, ≥ 3 edits) matching.

## Observability

- `dejavu report` / `bun scripts/doctor.ts [--repair]` — one-command health check over every invariant the data model implies (gate shape, policy violations, index↔gates consistency, secrets, version drift, flappy gates); `--repair` heals first, idempotent.
- `bun scripts/analyze.ts` — store summary: statuses, tools, top patterns.
- `dejavu lesson list` / `dejavu lesson set <key> "<one-line fix>"` — replace machine-default corrections with human ones; `lesson set` doubles as the review doctor asked for.
- `/dejavu` inside OpenCode — doctor first, then the report.
- `DEJAVU_DEBUG=1` — engine log lines on stderr (stdout always stays pure JSON). Every event is logged to `log.jsonl` with its channel and version — see [reference — observability](docs/reference.md#observability-and-maintenance).

## Configuration

### Environment overrides

`DEJAVU_HOME` moves both store dirs; `DEJAVU_DEBUG=1` prints hook-CLI diagnostics to stderr. The opt-in recovery flags enable at `1`/`true`/`yes` (default off); the enforcement tunables below can be overridden per process without editing source — each is read once at startup and falls back to its default when the value is not an integer within bounds:

| Variable | Default | Bounds | Effect |
|---|---|---|---|
| `DEJAVU_LEAK_RECOVERY` | off | flag | opt in to leaked tool-call recovery in the repeat channel (OpenCode hosts) |
| `DEJAVU_LOOP_RECOVERY` | off | flag | opt in to stuck-reasoning loop recovery: abort + corrective user turn (OpenCode hosts) |
| `DEJAVU_TTL_DAYS` | 60 | 1–3650 | days without recurrence before a gate expires |
| `DEJAVU_NOISE_TTL_DAYS` | 7 | 1–365 | TTL for one-off patterns (`watching`, count ≤ 1) |
| `DEJAVU_PROMOTE_COUNT` | 3 | 1–100 | failures before a bash pattern becomes a gate |
| `DEJAVU_PROMOTE_COUNT_PROBE` | 5 | 1–100 | failures before a probe tool becomes a gate |
| `DEJAVU_PROMOTE_SESSIONS` | 2 | 1–100 | distinct sessions required to promote |
| `DEJAVU_HEAL_SUCCESSES` | 3 | 1–100 | consecutive successes that retire a gate |
| `DEJAVU_DEMOTE_RECURRENCES` | 3 | 1–100 | post-gate recurrences that demote a gate |
| `DEJAVU_DEMOTE_OVERRIDES` | 3 | 1–100 | explicit bypasses that demote a blocking gate |
| `DEJAVU_TAUGHT_REMINDERS` | 5 | 1–100 | reminders with zero reoffense that retire a gate as taught |
| `DEJAVU_SNOWBALL_CHAIN_MIN` | 3 | 1–100 | consecutive prefix-growth bash calls before the snowball guard interrupts |

### Data files

| File | Contents |
|---|---|
| `~/.config/opencode/dejavu/gates.json` | global gates (agent habits) |
| `~/.config/opencode/dejavu/index.json` | cross-project pattern index: which project dirs each failure key was seen in (escalation evidence) |
| `<repo>/.opencode/dejavu/gates.json` | project gates (repo gotchas) |
| `*/dejavu/log.jsonl` | every event: detected, promoted, reminded, retry-allowed, blocked, override, expired, recurred-after-gate, healed, retired, demoted, repaired, quarantined, degraded, init |
| `*/dejavu/*.corrupt*` | quarantined corruption — bytes preserved for forensics; safe to delete after inspection |

The store paths are historical (`.opencode/`) but the store is harness-neutral — ALL harnesses share it. Both files are human-editable ([see above](#what-a-gate-looks-like) for the record shape). Clearing `feedbackDemoted` (and setting `status` back) re-enforces a gate the agent's behavior retired — it gets a fresh grace window via `feedbackBaseline`.

Project stores keep themselves out of `git status`: init writes a self-ignoring `.opencode/dejavu/.gitignore` — `gates.json` is designed to be committable (shared repo gotchas), runtime files (log, index, locks, tmp) are ignored. A root-level `.gitignore` rule for `.opencode/` overrides the nested re-include — repos that ignore `.opencode/` at the root must adjust their ignore rules to actually commit `gates.json`.

## Comparison with analogs

Landscape survey (Sep 2026, ~60 OSS projects + native features checked). The space splits into two camps that never intersect: **guardrail/hook engines** intercept and block tool calls, but only evaluate human-authored static policies per call — no failure memory, nothing learned; **memory/learning plugins** persist and extract across sessions, but only inject context into the prompt — none ever blocks a tool call. dejavu is currently the only shipped project closing the loop mechanically: observe failures → promote an enforceable gate → remind/block → heal/demote from behavior.

| Product | Learns rules from observed failures | Enforces / blocks tool calls | Mechanical hot path (no LLM) |
|---|---|---|---|
| **dejavu** | ✅ mechanical promotion | ✅ remind→block escalation | ✅ |
| Cupcake · agentjail · cc-safety-net · probity · guardrails packs | ❌ human-authored policy | ✅ deny | ◐ |
| claude-mem · claude-smart · supermemory · opencode-mem · harness-memory | ◐ LLM-extracted, injected only | ❌ | ❌ |
| sinapsis (archived) · harness-forge · projectmem · open-bias | ◐ counted or classified | ❌ advisory only | ◐ |
| NeMo Guardrails · Guardrails AI · LLM gateways | ❌ | ❌ proxy-level | ❌ |
| Claude Code native permissions | ❌ static allow/deny | ◐ | ✅ |

### Where dejavu is worse (honest gaps)

- **Semantic identity.** Two syntactically different calls solving the same broken thing (`pnpm tsc --noEmit` vs `npm run typecheck`) land on different keys; fuzzy merge is Levenshtein ≤ 0.3 with a ≥ 3-edit floor by design. LLM-driven memory tools collapse such variants at extraction cost — dejavu pays precision for determinism.
- **Rule expressiveness.** Gates key on tool-call signatures only. Human-authored policy engines (Rego in Cupcake/agentjail, rulebooks in cc-safety-net, `probity.config.ts`) can express arbitrary conditions — file paths, tenant isolation, PII, "never touch prod" — that dejavu cannot represent. dejavu deliberately does not try to be a security sandbox; those tools are complementary, not competitors.
- **Conversational memory.** claude-mem/claude-smart/supermemory recall decisions, preferences, and project history; dejavu remembers exactly one thing: failing calls. Composable — they occupy orthogonal storage.
- **Traction.** claude-mem (~95k★), claude-smart (~800★), abide (~400★) vs a young repo here.

Adjacent-by-name, not competitors: ast-grep / Semgrep-style linters (static code content vs runtime tool calls), NeMo Guardrails / LLM gateways (prompt policing at the proxy, never see the tool pipeline), Reflexion (research, never shipped), post_compact_reminder (static hook), hook SDKs (authoring frameworks), native platform permissions (static halves only — the anthropics/claude-code#34556 persistent-memory request was closed unimplemented).

## Stats

The honest answer: dejavu does not ship benchmark numbers, and this section will not invent any. What exists is your own store — every host writes `log.jsonl`, so the evidence is local, per-agent, and auditable.

All-time contents of one developer's global store as of Sep 29, 2026 — 6574 events on 40 active days, across 11 project dirs and every harness sharing that store: 3931 `detected` failures (2431 distinct keys), 237 `promoted` (211 distinct keys), 163 `recurred-after-gate`, 56 `blocked`, 383 `override`, 11 healed / 46 retired-taught / 30 demoted. 62 of the 211 promoted keys recurred after their gate existed — recurrence-after-gate is the per-gate health signal, and demotions plus retirements are the loop closing in both directions. One person's agent habits over six weeks is a sample size of one; treat it as an example of what the data looks like, not as proof.

**Measure it yourself** — after N sessions of real use:

```bash
dejavu report            # doctor over project + global stores
bun scripts/analyze.ts   # statuses, tools, top patterns
```

or run `/dejavu` inside OpenCode. If your numbers say the approach is wrong, the data will show it — that is the point of the metric.

## Roadmap

- Windsurf / Amp adapters — blocked on usable context-injection surfaces (block-only today); the adapter slots exist
- recurrence-after-gate reporting command; `tool.execute.error` (opencode issue #27900) closed upstream as not planned — event-channel detection remains the supported path
- auto-proposal of ast-grep rules for statically detectable patterns (repo-level CI gates)
- embedding-assisted candidate merging for semantic near-duplicates (advisory only — the enforcement decision stays mechanical; addresses the semantic-identity gap above)
- semantic mapping table — a maintained synonym table (`pnpm tsc` ↔ `npm run typecheck`) feeding the existing mechanical fuzzy merge; advisory only, same as embeddings
- `dejavu share` — export/merge portable gate bundles between machines and teams (opt-in; gates are already harness-neutral JSON, the command makes moving them explicit)
- docs-as-code — generate the gate/correction reference from the store schema instead of hand-maintained prose that drifts from `validate.ts`

## Development

```bash
bun install
bun run typecheck          # tsc --noEmit (index.ts, src/**, scripts/**, test/**)
bun test/smoke.ts          # full behavioral test (drives the OpenCode plugin hooks)
bun test/enforce.ts        # engine characterization (harness-agnostic core)
bun test/adapters.ts       # adapter mapping + decision dialects
bun test/cli.ts            # CLI end-to-end (spawn, promotion, block/annotate, fail-open)
bun test/language-gaps.ts  # language-ecosystem coverage of patterns.ts
bun test/guards.ts         # proactive guards characterization (fire shapes, precedence, bypass)
bun test/messages.ts       # teaching-text framing (tier-truthful, data-label, correction bound)
bun test/property.ts       # seeded generator: normalization/fuzzy invariants
bun test/fuzz.ts           # mutation fuzz: no crash, no invariant break
bun test/env.ts            # DEJAVU_* env overrides: resolved tunables + promotion effect
bun run lint:ast           # ast-grep structural gates (needs ast-grep on PATH)
```

Architecture: `src/patterns.ts` + `src/store.ts` + `src/validate.ts` (pure engine + persistence), `src/enforce.ts` + siblings (harness-agnostic enforcement: `enforceBefore`/`enforceAfter`/`recordEventFailure`/`cleanupSession` over `EnforceContext`), `src/adapters/` (payload ↔ contract mapping per harness), `src/cli.ts` (hook-handler entry for external harnesses), `index.ts` (OpenCode plugin host). Tunables are named constants at the top of their modules.

Structural gates live in `.ast-grep/rules/` (run by `bun run lint:ast` and CI): `no-load-force-flag` forbids `load(true)`/`loadIndex(true)`; `no-raw-gates-splice` forbids raw splices on gate arrays.

## Disclaimer

dejavu is a community project. It is not built by, and not affiliated with, the OpenCode, Anthropic, OpenAI, Google, Anysphere (Cursor), GitHub, or Charm teams.

## License

MIT
