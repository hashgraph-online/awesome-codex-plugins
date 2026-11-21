---
name: diamond-render
description: Render `.claude/diamonds/active.yml` as the decisions each diamond has recorded, in order, grouped by mode (discovery, delivery). Read-only. Default format Mermaid stateDiagram-v2, drawn by a script. Recommended at the end of `/mycelium:diamond-assess` so every assessment closes with a visual state-of-play. See `${CLAUDE_PLUGIN_ROOT}/engine/render-conventions.md` for shared render fleet conventions.
metadata:
  instruction_budget: "40"
  framework_dependency: "mycelium"
  framework_dependency_note: "Reads .claude/diamonds/active.yml through ${CLAUDE_PLUGIN_ROOT}/scripts/render_diamonds.py. Standalone use will fail without active.yml present."
  identifier_exposure: "NONE"
---

# Diamond Render

Read-only render of `.claude/diamonds/active.yml`. First specialist of the render fleet (with
`/mycelium:ost-render`, `/mycelium:cycle-render` and the dispatcher `/mycelium:render`).

**What it draws (v0.309.0, stage 5d-3, founder ruling DL-1372 V4).** Each diamond as the decisions
it has recorded, in the order recorded, with their dates, under the mode the diamond was in when it
took them: discovery until `commit_to_build`, delivery after (DL-1368 S1). Then the decisions still
to come, marked `(next)`. A loop iterates by appending (DL-1373), so a second `start_experiment` is
drawn as its own step where it happened, and the position does not move back. An L0 is not a loop:
it states its purpose (`state_purpose`) and reviews it (`review`). Until v0.309.0 this skill asked
the agent to draw four phases with transition labels of its own; the record has been decisions
since v0.306.0, and the picture is now drawn from them by code.

## When NOT to use

- To record a decision (move a diamond on) → `/mycelium:diamond-progress`.
- To score gates against current evidence → `/mycelium:diamond-assess`.
- To start a new diamond → `/mycelium:start`.

## Identifier exposure

**Declared**: NONE

### Scope (canvas surfaces touched)

| Canvas file | Identifier-bearing fields | Frequency |
|---|---|---|
| `.claude/diamonds/active.yml` | none in current schema (v1) | n/a |

### Rationale

`diamonds/active.yml` holds decisions, dates, gate statuses, scale and confidence. No contributor
names, no participant fields, no identifier-bearing prose. Zero identifier exposure as of v0.40.0.

**Future-schema-change caveat**: if a future schema adds an identifier field (e.g., per-team diamond
ownership for multi-team Mycelium per the deferred Team Topologies adoption), this declaration
becomes false. The skill must then be re-declared `YES` or `MIXED`, consult the registry per
`engine/render-conventions.md#hard-rule-consent--privacy-gate`, and ship redaction fixtures. The
schema-versioning rule surfaces the schema_version mismatch at runtime as a forcing function for the
re-audit.

### Anon-label convention

Not applicable (NONE).

### Worked example

```
L3 Test: committed to build (delivery)  conf=0.4
================================================
  [discovery]
    * set_target 2026-09-03
    * start_experiment 2026-09-04
  [delivery]
    * commit_to_build 2026-09-04
    * start_experiment 2026-09-10
    . release (next)
    . close (next)
```

No identifiers anywhere in the output, regardless of audience.

### Fixture pointer

Not applicable. Check 43 forbids redaction fixtures on NONE-declared specialists (avoids the
"declares NONE but acts YES" drift). The behaviour is tested in `tests/python/test_render_diamonds.py`.

## Arguments

| Arg | Default | Values | Effect |
|---|---|---|---|
| `--format` | `mermaid` | `mermaid` \| `ascii` \| `json` | Output format. `markdown-table` and `markdown-list` are not supported (a state diagram does not map to them); the script fails loud per `engine/render-conventions.md#format-support-negotiation-global-rule`. |
| `--scale` | `active` | `L0`-`L5` \| `active` \| `all` | Which diamonds. `active` = the open ones (in `active_diamonds`, not closed, parked, killed, archived or retargeted, and no `close` recorded); `all` adds completed and archived. |
| `--theme` | `base` | `base` \| `dark` | `dark` is the WCAG-by-construction opt-in per `engine/render-conventions.md#wcag-aa-theme-convention`. |
| `--no-gates` | off | flag | Leave out each decision's gates and their status (ascii and json). Mermaid never draws them: it places a note on a nested state across the page. |
| `--no-confidence` | off | flag | Leave out the diamond's `confidence`. |

## Workflow

### Step 1: Draw it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_diamonds.py" --project-dir . [--format ...] [--scale ...]
```

Show its output as it is. Do not redraw it by hand, rename decisions, or add states, gates or
values the record does not hold: two renders of one record must be the same picture. Exit 2 means a
format it does not draw, a scale with no diamond, or a diamonds file it cannot read; say which.

### Step 2: Staleness check

Per `engine/render-conventions.md#staleness-check-distinction`: compare the diamonds file's
canvas-state timestamp (`_meta.last_validated`, else top-level `last_updated:`) with the most recent
decision-log entry mentioning a drawn diamond. If the decision log is newer, put the staleness
warning above the render.

### Step 3: Validate the Mermaid (mermaid format)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_diamonds.py" --project-dir . \
  | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_mermaid.py" -
```

It checks state-id consistency (F11) and WCAG AA contrast (F13); add `--cli` for a full parse when
`mmdc` is present. Exit 1: do not show the diagram; report the failure, which is a defect in the
script. Visual layout still needs a human eye, which is why the disclaimer stays.

### Step 4: Disclaimers

Per `engine/render-conventions.md`:

- **Lossy-on-export** (mermaid + ascii): dropped fields: each decision's `ruling` and `note`, the
  diamond's `progression_blockers`, `closes_on`, and the decision log's prose; mermaid also drops the
  gates.
- **Canonical disclaimer**: final block. `stateDiagram-v2` is stable; no beta warning.
- **mermaidchart.com handoff**: appended for `--format mermaid` only.

## Rules

1. **Read-only.** Never modify active.yml, the decision log, or any state.
2. **The script draws; the agent does not.** No hand-drawn variant, no renamed decision, no state or
   gate the record does not hold.
3. **Empty case**: no open diamond prints `No open diamond: run /mycelium:start.` and exits 0.
4. **`--as-of` is not offered.** The decision log records each decision's date, so a past state is
   the decisions dated on or before that day; this render does not filter by date yet, and it does
   not pretend to.

## Counter-Argument Check

Before showing it:

1. *"Is this the record, or has the diamonds file been edited since the last decision?"* Step 2 is
   the mechanical answer.
2. *"Am I drawing one diamond when the decision log mentions others?"* If `--scale active` drew one
   and the log names more, say: `Other diamonds in active.yml are closed or not open: --scale all
   draws them.`

## What this skill does NOT do

- Does NOT record a decision. That's `/mycelium:diamond-progress`.
- Does NOT score gates against current evidence. That's `/mycelium:diamond-assess`.
- Does NOT explain WHY a diamond is where it is. That lives in the decision log and the
  diamond-assess output.

## Recommend-not-invoke from `/mycelium:diamond-assess`

`/mycelium:diamond-assess` ends its decision output with:

```
> _Visualize the assessed state: run `/mycelium:diamond-render`. The canvas
> remains source of truth; this render is a snapshot._
```

NOT a silent sub-invocation. User retains one-hop control.

## Tests

`tests/python/test_render_diamonds.py`: a repeated decision drawn where it happened (DL-1373); a
`close` in the mode it is taken in; an L0 that states and reviews; `active` against `all`; the
Mermaid valid, with each state inside its mode (the first draft drew every decision outside it);
unsupported formats and scales failing loud; the empty case. Until v0.309.0 this section listed
seven fixtures under `tests/bash/fixtures/diamond-render/` that were never written.

## Theory citations

- Rother (Toyota Kata): a target condition and experiments toward it, the loop each level runs
  (DL-1366). Recording each experiment by appending, never editing, is this framework's ruling
  (DL-1373), not Rother's
- Cagan / Patton (dual-track): discovery and delivery as two modes running in parallel. Reading the
  switch off `commit_to_build` is this framework's (DL-1368 S1)
- Hick's Law (one recommended format default; explicit fail-loud on unsupported)
- WCAG 2.1 AA (contrast bar for human-audience rendering; `engine/render-conventions.md#wcag-aa-theme-convention`)
