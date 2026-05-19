# Spawning Judges

## Capability Contract

Council requires these runtime capabilities. Map them to whatever your agent harness provides.

**For concrete tool call examples per backend, read the matching shared reference:**
- Codex Sub-Agents / CLI → `skills/shared/references/backend-codex-subagents.md`
- Background Tasks → `skills/shared/references/backend-background-tasks.md`
- Inline → `skills/shared/references/backend-inline.md`

| Capability | Required for | What it does |
|------------|-------------|-------------|
| **Spawn parallel subagent** | All modes except `--quick` | Create N judges that run concurrently, each with a prompt |
| **Agent-to-agent messaging** | `--adversarial` only | Send a message to a running judge (for R2 verdict exchange) |
| **Graceful shutdown** | Cleanup | Terminate judges after consolidation |
| **Shared filesystem** | All modes | Judges write output files to `.agents/council/` |

If **spawn** is unavailable, degrade to `--quick` (inline single-agent).
If **messaging** is unavailable, `--adversarial` degrades to single-round review.
If **Codex CLI** is unavailable AND `--mixed` is set, emit a hard error and
exit without spawning judges (strict — see "Strict Codex Requirement" below).
`--mixed` never silently degrades to Claude-only.

## Spawning Flow

### Phase 1: Spawn Judges in Parallel

For each judge (N = 2 default, 3 with `--deep`, 2N with `--mixed`):

1. Spawn a subagent with the judge prompt (see `agent-prompts.md`)
2. Each judge receives the full context packet as its prompt
3. Track the mapping: `judge-{N}` → agent handle (for messaging and cleanup)

All judges spawn in parallel. Do not wait for one before spawning the next.

#### Mixed-Mode Perspective Distribution

When `--mixed` is set:

1. Build the perspective list once from `--preset`, `--perspectives`, or `--perspectives-file`. If none of these is set, treat the list as `[default, default, default]` (3 generic slots).
2. For each perspective P in the list, spawn EXACTLY ONE Claude judge AND ONE Codex judge, both receiving:
   - the same packet (see "Pre-assemble packet" pattern)
   - the same `{PERSONA_NAME}` and `{PERSPECTIVE}` slot in the agent prompt
   - the same `output_schema`
3. Total judges = 2 × len(perspectives). Default len=3 → 6 judges. Variable preset sizes scale naturally (e.g., `--preset=security-audit` has 4 perspectives → 8 judges; `--preset=plan-review` has 4 → 8; `--preset=leadership-quartet` has 4 → 8).
4. Do **NOT** split perspectives across vendors. The whole point of `--mixed` is to hold the perspective constant and vary only the vendor — that is what makes verdict differences attributable to the vendor instead of to the perspective.

### Phase 2: Wait for Completion

Judges write output files, then send a MINIMAL completion signal:

```json
{
  "type": "verdict",
  "verdict": "PASS | WARN | FAIL",
  "confidence": "HIGH | MEDIUM | LOW",
  "file": ".agents/council/YYYY-MM-DD-<target>-judge-1.md"
}
```

Wait for all judges to signal (up to `COUNCIL_TIMEOUT`, default 120s). If a judge times out, proceed with N-1 and note in report.

### Phase 3: Debate R2 (if `--adversarial`)

After R1 completes, send each judge a message containing:
- Verdict summaries of OTHER judges (verdict + confidence + file path only)
- Instructions to read other judges' files for full reasoning
- The debate protocol (see `agent-prompts.md`)

CONTEXT BUDGET: Send only verdict summaries, NOT full JSON findings. Judges read files for detail.

Wait up to `COUNCIL_R2_TIMEOUT` (default 90s). If a judge doesn't respond, use their R1 verdict.

### Phase 4: Consolidation

Lead reads each judge's output file (one at a time), extracts JSON verdict, synthesizes final report. No separate agent — consolidation runs inline.

### Phase 5: Cleanup

Shut down all judges via runtime's shutdown mechanism. Cleanup MUST succeed even on partial failures:

1. Request graceful shutdown for each judge
2. Wait up to 30s for acknowledgment
3. If any judge doesn't respond, log warning, proceed anyway
4. Always run cleanup — lingering agents pollute future sessions

## Codex CLI Judges (--mixed mode, paired)

For cross-vendor consensus, run Codex CLI processes alongside runtime-native judges. The Codex judges receive the **same** perspective list as the runtime-native judges (one Codex CLI process per perspective) — see "Mixed-Mode Perspective Distribution" above.

### Strict Codex Requirement (no silent fallback)

When `--mixed` is set, Codex CLI availability is **REQUIRED**. This is a strict,
hard-error contract — `--mixed` exists precisely to get cross-vendor validation,
so silently degrading to Claude-only would mask the intent the caller explicitly
paid for (see `na-1i9`: a pre-mortem session ran with `--mixed` and produced
Claude-only judges because the Codex path wasn't wired, and the operator never
saw that the cross-vendor check never happened).

Pre-flight (before spawning any judges):

1. `command -v codex` must resolve. If not: **hard error**, exit non-zero,
   do **not** spawn any judges.
2. `codex --version` must succeed. If not: **hard error**, same treatment.
3. If `COUNCIL_CODEX_MODEL` is set, verify the model is reachable with a
   dry `codex exec` smoke call. If not: **hard error**.

Required remediation message on any of the above failures:

```
error: council --mixed requires Codex CLI, but codex was not found (or not runnable).
  Fix one of:
    1. Install Codex CLI:   https://github.com/openai/codex
    2. Drop --mixed and re-run with Claude-only judges:   /council validate <target>
  Aborting without spawning judges.
```

**Do NOT silently fall back to Claude-only when `--mixed` is set.** That would
defeat the cross-vendor validation intent. The only acceptable degradation is
explicit operator action (dropping `--mixed`). This rule is strict by design.

Once Codex is confirmed available, spawn Codex judges alongside runtime-native
judges.

```bash
# With structured output (preferred)
codex exec -s read-only -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-{N}.json "{PACKET}"

# Fallback (if --output-schema unsupported — this is an output-format fallback,
# NOT a vendor fallback; Codex is still required)
codex exec --full-auto -C "$(pwd)" -o .agents/council/codex-{N}.md "{PACKET}"
```

Uses the user's default Codex model. Only pass `-m` if `COUNCIL_CODEX_MODEL` is explicitly set.

Flag order: `-s`/`--full-auto` → `-C` → `--output-schema` → `-o` → prompt (add `-m` before `-C` only if overriding model).

**Valid flags:** `--full-auto`, `-s`, `-m`, `-C`, `--output-schema`, `-o`, `--add-dir`
**Invalid flags:** `-q` (doesn't exist), `--quiet` (doesn't exist)

Codex CLI processes run as background shell commands — this is fine (they're separate OS processes, not agent background tasks).

## Timeout Configuration

| Timeout | Default | Description |
|---------|---------|-------------|
| Judge timeout | 120s | Max time for judge to complete (per round) |
| Shutdown grace period | 30s | Time to wait for shutdown acknowledgment |
| R2 debate timeout | 90s | Max time for R2 after sending debate messages |

## Model Selection

| Vendor | Default | Override |
|--------|---------|----------|
| Claude | sonnet | `--claude-model=opus` |
| Codex | (user's default) | `--codex-model=<model>` or `COUNCIL_CODEX_MODEL` env var |

## Output Collection

All council outputs go to `.agents/council/`:

```bash
mkdir -p .agents/council

# Judge output (R1)
.agents/council/YYYY-MM-DD-<target>-judge-1.md
.agents/council/YYYY-MM-DD-<target>-judge-error-paths.md

# Judge output (R2, when --adversarial)
.agents/council/YYYY-MM-DD-<target>-judge-1-r2.md

# Codex CLI output (--mixed)
.agents/council/YYYY-MM-DD-<target>-codex-1.json   # with --output-schema
.agents/council/YYYY-MM-DD-<target>-codex-1.md      # fallback

# Final consolidated report
.agents/council/YYYY-MM-DD-<target>-report.md
```

## Judge Naming

Convention: `council-YYYYMMDD-<target>` for the team/session name.

Judge names: `judge-{N}` for independent judges, `judge-{perspective}` when using presets (e.g., `judge-error-paths`, `judge-feasibility`).
