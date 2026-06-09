---
name: council
description: "Run council."
---
# $council — Multi-Model Consensus Council (Codex Native)

Spawn parallel judges with different perspectives via `spawn_agent`, consolidate into consensus.

## Quick Start

```bash
$council validate this plan                                    # verdict mode (the default)
$council --mode=brainstorm caching approaches                  # brainstorm mode
$council --mode=debate should we adopt event sourcing?         # debate mode (named personas duel)
$council --depth=quick validate recent                         # fast inline check
$council --roster=security-audit validate the auth system      # preset persona roster
$council --depth=deep --runtime=mixed --roster=leadership-quartet validate product thesis
```

## Modes — the deliberation taxonomy

`--mode` selects one of exactly three deliberation patterns; `verdict` is the default.

| `--mode` | Pattern | Synthesis |
|----------|---------|-----------|
| `brainstorm` | **diverge** — judges generate options independently before any cross-talk | ranked set of ideas, perspectives, risks (no PASS/WARN/FAIL) |
| `debate` | **contend** — independent positions → adversarial 0–1000 cross-scoring → reveal round | ranked decision with recorded dissent |
| `verdict` *(default)* | **converge** — judges judge the artifact against the bar independently | one PASS / WARN / FAIL with consolidated findings |

`verdict` runs when `--mode` is omitted. `validate` is a verdict alias; `research` folds into `brainstorm` (`--focus=research`). `--mode` is the deliberation *pattern*; `--focus`/`--depth`/`--runtime`/`--roster` are orthogonal knobs. Every mode runs the same lifecycle — convene → brief → deliberate → synthesize → record. Full taxonomy and knob aliases: `references/modes.md`. Per-phase debate-mode templates: `references/dueling-route.md`.

**Knob aliases:** `--depth=quick` (alias `--quick`) = single inline judge; `--depth=deep` (alias `--deep`) = 3 judges; `--runtime=mixed` (alias `--mixed`) = matched Claude+Codex pairs.

**Note:** `--adversarial` is a **verdict-mode intensifier** (2 adversarial rounds), not the `debate` mode — it requires agent messaging. Use `spawn_agent` plus `send_input` for one-off follow-up only; do not rely on multi-round rounds without messaging support.

**Note:** `--mixed` is strict. Pre-flight `codex` and `codex --version` before spawning any judges; if Codex CLI is missing or not runnable, hard-error and tell the operator to install/fix Codex CLI or drop `--mixed`. Never silently convert `--mixed` into runtime-native-only judging.

**Note:** `--profile=<name>` follows the shared model-profile contract: `balanced`, `budget`, `fast`, `inherit`, `quality`, `thorough`. See `references/model-profiles.md`.

| Env var | Default |
|---------|---------|
| `COUNCIL_CLAUDE_MODEL` | sonnet |
| `COUNCIL_EXPLORER_MODEL` | sonnet |
| `COUNCIL_CODEX_MODEL` | unset; use Codex default (`gpt-5.5` recommended when available) |
| `COUNCIL_TIMEOUT` | 120 |
| `COUNCIL_EXPLORER_TIMEOUT` | 60 |
| `COUNCIL_R2_TIMEOUT` | 90 |

| Flag | Description |
|------|-------------|
| `--technique=<name>` | Brainstorm technique (reverse, scamper, six-hats). See `references/brainstorm-techniques.md`. |
| `--profile=<name>` | Model quality profile (balanced, budget, fast, inherit, quality, thorough). See `references/model-profiles.md`. |

## Mode inference (trigger words)

When `--mode` is omitted, infer the mode from the prompt; `verdict` is the fallback.

| `--mode` | Trigger Words | Focus |
|----------|---------------|-------|
| **verdict** *(default)* | validate, check, review, assess, critique | Is this correct? What's wrong? |
| **brainstorm** | brainstorm, explore, options, approaches; research, investigate, deep dive, analyze | Alternatives, trade-offs, structure? |
| **debate** | debate, duel, decide, "have <experts> decide", "council of <names>" | Which option wins when named experts cross-score? |

`validate` is a verdict alias; the `research` verb folds into **brainstorm**.

## Execution Flow

### Phase 1: Build Packet

1. Determine task type from user prompt
2. Identify target (files, diffs, plan, code)
3. Read relevant context files
4. Select perspectives (or use preset)

### Phase 1a: Spawn Judges

Use one `spawn_agent` call per judge. Include the same context packet in each prompt and assign a distinct perspective.

**Mixed-mode pairing (--mixed only):** For `--mixed`, build the perspective list once. For each perspective, spawn ONE `spawn_agent` call AND ONE `codex exec` process with the SAME perspective string, SAME packet, SAME prompt — only the vendor differs. The pair holds perspective constant and varies only the vendor, enabling head-to-head cross-vendor comparison per perspective. Do NOT split perspectives across vendors (e.g., do NOT give Claude judges perspectives 1-3 and Codex judges perspectives 4-6). Total judges = 2 × len(perspectives); default = 6.

```text
spawn_agent(message="You are judge-1.

Perspective: correctness

Task: validate the following target.
Target files: ...
Context: ...

Write your full analysis to .agents/council/judge-1.md and your verdict to the final paragraph.")

spawn_agent(message="You are judge-2.

Perspective: completeness

Task: validate the following target.
Target files: ...
Context: ...

Write your full analysis to .agents/council/judge-2.md and your verdict to the final paragraph.")
```

With `--mixed`, spawn the runtime-native judges above plus 3 Codex CLI judges. Codex CLI judges write under `.agents/council/codex-{N}.json` when `--output-schema` is supported, or `.agents/council/codex-{N}.md` as an output-format fallback only. See `references/cli-spawning.md` for the strict pre-flight and command shape.

### Step 1b: Load Project Reviewer Config

Check for project-level reviewer configuration before spawning judges:

```bash
REVIEWER_CONFIG=".agents/reviewer-config.md"
if [ -f "$REVIEWER_CONFIG" ]; then
    # Parse YAML frontmatter for reviewer list
    # Use reviewers/plan_reviewers/skip_reviewers to select judge perspectives
fi
```

If `reviewer-config.md` exists:
- Use `reviewers` list to select which judge perspectives to spawn
- Use `plan_reviewers` for plan validation specifically
- Use `skip_reviewers` to exclude perspectives even if preset includes them
- Pass markdown body as additional context to all judges

If no config exists, use defaults (current behavior unchanged).

For schema details and an example, see `references/reviewer-config-example.md`.

### Phase 1b: Wait for Judges

```
wait_agent(targets=["agent-id-1", "agent-id-2"])
```

If a judge needs follow-up, use `send_input` on that agent. If a judge stalls, `close_agent` it and proceed with the remaining responses.

### Phase 2: Consolidation (Lead — Inline)

The lead reads each judge's output file and synthesizes:

1. Read each `.agents/council/judge-*.md` file
2. Compute consensus verdict:
   - **PASS:** All judges PASS (or majority PASS, none FAIL)
   - **WARN:** Any judge WARN, none FAIL
   - **FAIL:** Any judge FAIL
   - Core rules: All PASS -> PASS; Any FAIL -> FAIL; Mixed PASS/WARN -> WARN; cross-vendor disagreement -> DISAGREE.
3. Identify shared findings across judges
4. Surface disagreements with attribution
5. Generate final report

### Phase 3: Write Report

Save to `.agents/council/YYYY-MM-DD-<type>-<target>.md`:

```markdown
# Council Report: <type> <target>

**Consensus:** PASS/WARN/FAIL
**Judges:** N responded / N spawned
**Date:** YYYY-MM-DD

## Shared Findings
- Finding 1 (judges 1, 2)
- Finding 2 (judges 1, 3)

## Disagreements
- Judge 1 says X, Judge 2 says Y

## Recommendations
1. ...
2. ...

## Individual Verdicts
| Judge | Perspective | Verdict | Confidence | Findings |
|-------|-------------|---------|------------|----------|
| judge-1 | correctness | PASS | high | 3 |
| judge-2 | completeness | WARN | medium | 5 |
```

## Presets

| Preset | Perspectives |
|--------|-------------|
| default | correctness, completeness |
| security-audit | vulnerability, attack-surface, data-flow |
| architecture | coupling, scalability, maintainability |
| research | breadth, depth, contrarian |
| ops | reliability, observability, failure-modes |
| leadership-quartet | product-manager, cto, chief-engineer, staff-engineer |

Use: `$council --preset=security-audit validate the auth system`
Use: `$council --deep --mixed --preset=leadership-quartet validate product thesis`

## Graceful Degradation

| Failure | Behavior |
|---------|----------|
| 1 of N judges timeout | Proceed with N-1, note in report |
| All judges fail | Return error, suggest retry |
| No multi-agent capability | Fall back to `--quick` (inline) |

## Context Budget Rule

Judges write ALL analysis to output files. Results to the lead contain ONLY minimal signals. This prevents N judges from flooding the lead's context.

## Standards Integration

If `$standards` is available and the target includes code files, load applicable language standards and include them in each judge prompt.

## First-Pass Rigor Gate (verdict mode)

When validating plans/specs, judges must check:
1. Mutation + ack sequence is explicit and non-contradictory
2. Consume-at-most-once path is crash-safe
3. Status/precedence behavior has field-level truth table
4. Conformance includes boundary failpoint tests

Missing gate item → minimum WARN. Critical unverifiable invariant → FAIL.

## Reference Documents

- [references/modes.md](references/modes.md)
- [references/dueling-route.md](references/dueling-route.md)
- [references/model-routing.md](references/model-routing.md)
- [references/agent-prompts.md](references/agent-prompts.md)
- [references/backend-background-tasks.md](references/backend-background-tasks.md)
- [references/backend-codex-subagents.md](references/backend-codex-subagents.md)
- [references/backend-inline.md](references/backend-inline.md)
- [references/brainstorm-techniques.md](references/brainstorm-techniques.md)
- [references/caching-guidance.md](references/caching-guidance.md)
- [references/cli-spawning.md](references/cli-spawning.md)
- [references/adversarial-protocol.md](references/adversarial-protocol.md)
- [references/explorers.md](references/explorers.md)
- [references/finding-extraction.md](references/finding-extraction.md)
- [references/model-profiles.md](references/model-profiles.md)
- [references/output-format.md](references/output-format.md)
- [references/personas.md](references/personas.md)
- [references/presets.md](references/presets.md)
- [references/quick-mode.md](references/quick-mode.md)
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md)
- [references/reviewer-config-example.md](references/reviewer-config-example.md)
- [references/strategic-doc-validation.md](references/strategic-doc-validation.md)
