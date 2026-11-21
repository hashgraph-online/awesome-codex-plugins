---
name: scaffold-cost-check
description: "Measure Mycelium's own scaffold token cost (CLAUDE.md + engine + harness + canvas + memory) and surface a structured estimate. One-shot audit; pair with /framework-health for trend tracking."
metadata:
  instruction_budget: "42"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Scaffold Cost Check

Measure the token cost of Mycelium's stable scaffolding — the context surface loaded at SessionStart and on routine canvas/memory reads — so claims about "negligible overhead" are auditable. Datadog's *State of AI Engineering* (2026) reports ~69% of input tokens across production agents are system prompts; this skill makes Mycelium's analogous number visible.

## When to Use

- First-time audit on a project to compare actual scaffold cost against any "~6K negligible" claim in landscape/positioning.
- Periodic refresh via `/mycelium:framework-health` (see Wiring below).
- Before adding a new canvas file or harness doc that joins the stable load surface, to surface the marginal cost.

## Preflight: Read target canvas file(s) before any Write/Edit

Hard rule. Before issuing `Write` or `Edit` against any `.claude/canvas/*.yml`, use the **Read tool** on that file in this session. This skill only WRITES if explicitly asked to persist its output to `dora-metrics.yml#apex.scaffold_token_estimate`; default behavior is print-only.

## Workflow

1. **Inventory the stable scaffold surfaces** in the current project's plugin cache (or fall back to `.claude/` for legacy installs):
   - `CLAUDE.md` (project-local; the dispatcher)
   - `${CLAUDE_PLUGIN_ROOT}/engine/` (all `.md` and `.yml`)
   - `${CLAUDE_PLUGIN_ROOT}/harness/` (all `.md`)
   - `AGENTS.md` (project-local, if present — the router for non-Claude-Code runtimes; **not** a plugin file. It lives at a repo root and is never packaged, so resolving it through the plugin cache always missed and the row silently vanished from the table via the "if present" clause. Report `0 / absent` explicitly when the project has none, rather than omitting the row — an omitted row reads as "not part of the surface" instead of "not there")
   - `.claude/canvas/` (project state — not framework, but it ALSO joins the load surface; report separately)
   - `.claude/memory/` (corrections.md, patterns.md, MEMORY.md)
2. **Sum bytes** per surface via `wc -c`.
3. **Convert bytes → tokens** via the 4-bytes-per-token heuristic (±15% for English markdown across OpenAI/Anthropic tokenizers). Document the heuristic + the uncertainty band in the output.
4. **Render the output block** (see Output below).
5. **Optional: persist to canvas** if the user passes `--write`. Path: `.claude/canvas/dora-metrics.yml#apex.scaffold_token_estimate`. Follow the Postflight discipline below.

## Postflight: Verify-After-Write (write-narration-verification discipline)

If `--write` was passed, before claiming "✅ persisted to dora-metrics.yml", use the **Read tool** on `dora-metrics.yml` after the edit to confirm `apex.scaffold_token_estimate.total_tokens` actually carries the new number. AP#7 instance #18 (2026-06-05) is the worked failure mode this discipline prevents.

## Output

```
## Mycelium Scaffold Cost Audit

**Method**: byte-count ÷ 4 (heuristic; ±15% for English markdown).
**Measured**: <date>

| Surface | Bytes | Est. tokens |
|---|---|---|
| CLAUDE.md (project) | <b> | <t> |
| Plugin engine/ | <b> | <t> |
| Plugin harness/ | <b> | <t> |
| AGENTS.md | <b> | <t> |
| Canvas (.claude/canvas/) | <b> | <t> |
| Memory (.claude/memory/) | <b> | <t> |
| **Total stable surface** | <B> | **<T>** |

**Honest framing**: compare against any documented "~6K negligible" or similar claim in landscape/positioning. If actual is materially above (>2×), surface as a positioning correction.

**Goodhart pair**: scaffold_token_estimate ↔ first-pass-success-rate. Cutting scaffold to lower the number is only a win if first-pass quality doesn't drop. Track the pair.

**Sources**:
- [S5] Datadog, *State of AI Engineering* (2026): ~69% input tokens are system prompts across production agents.
- [S2] Faros, *Harness Engineering* (2026): staged measurement plan — start with metrics whose raw data exists.
```

## Canvas Output (only if `--write`)

Target: `.claude/canvas/dora-metrics.yml#apex.scaffold_token_estimate`

```yaml
apex:
  scaffold_token_estimate:
    claude_md_tokens: <n>
    engine_docs_tokens: <n>
    harness_docs_tokens: <n>
    agents_md_tokens: <n>
    canvas_tokens: <n>
    memory_tokens: <n>
    total_tokens: <n>
    method: "byte-count ÷ 4 (heuristic; ±15%)"
    last_measured: <date>
    compared_against_claim: "<found / not found>; <within / above / below>"
```

## Decision Log (MANDATORY if `--write`)

If persisting to canvas, append a decision-log entry referencing this skill's run, the measured total, and the comparison-against-prior-claim outcome. Source-tag with [S5] Datadog.

## Wiring

- Standalone: invoke as `/mycelium:scaffold-cost-check` (print-only) or `/mycelium:scaffold-cost-check --write` (persist).
- Trend tracking via `/mycelium:framework-health`: that skill's "Goodhart pair" check may reference this surface once a baseline exists. Not auto-invoked in v0.39.19 (sequenced for next minor); operator invokes manually until then.

## Rules

- Print-only by default; `--write` is opt-in.
- Heuristic-tokens carry ±15% explicitly in the output — do not narrate as exact.
- If the actual number is materially above a prior documented "negligible" claim, surface as a positioning correction back to landscape.yml or wherever the prior claim lived. Source-tag [S5].

## Theory Citations

- **Datadog 2026** ([S5]): production runtime telemetry — system prompts dominate input tokens; scaffolding cost is real and frequently unmeasured.
- **Faros 2026** ([S2]): staged measurement plan — compute from existing raw data before adding new instrumentation.
- **Goodhart's Law**: a token-count metric becomes a target once named; the counter-metric (first-pass-success) is required to prevent quality degradation in pursuit of token reduction.
