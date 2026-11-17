---
name: receipt-render
description: Render a completed diamond's work as a shareable, factual one-page "work receipt" (problem framed, assumptions tested, what was killed vs kept) carrying an origin line + a volitional onward-handoff data flow. Read-only. Consults the attribution registry per `${CLAUDE_PLUGIN_ROOT}/engine/render-conventions.md` consent + privacy gate. Follows the render fleet's shared conventions + consent gate (Check 43 applies via the `-render` name); a standalone shareable-artifact generator, NOT a `/render` dispatcher target. Audience fixed `external` (a hand-it-over artifact).
metadata:
  instruction_budget: "65"
  framework_dependency: "mycelium"
  framework_dependency_note: "Reads .claude/diamonds/active.yml + .claude/canvas/{archived-solutions,opportunities,cycle-history}.yml + .claude/harness/decision-log.md + attribution registry (env var $MYCELIUM_ATTRIBUTION_REGISTRY preferred; .claude/memory/attribution-registry.yml fallback). Standalone use will fail without a completed diamond present."
  identifier_exposure: "YES"
---

# Receipt Render

Read-only render of a **completed diamond** as a shareable, factual one-page **work receipt** — the problem as it was framed, the assumptions tested, what was killed and what was kept. It follows the render fleet's shared conventions and consent gate (`${CLAUDE_PLUGIN_ROOT}/engine/render-conventions.md`; Check 43 applies via the `-render` name), but unlike the diagram specialists (`diamond-render` / `ost-render` / `cycle-render`) it produces a shareable prose artifact and is **not** a `/mycelium:render` dispatcher target.

The receipt is a **carrier the user may choose to hand to a colleague**. It is generated fully **locally** — nothing is transmitted. Its footer carries a volitional data flow (an origin line + a pre-filled GitHub Discussion deep-link) so that, *if the user chooses*, the work can surface back to the maintainer. The skill never posts anything; a human reviews a draft and submits it.

## Why this exists (the honest framing)

A silent adopter is invisible to a solo maintainer. This skill does not generate adoption and does not phone home. It gives a real piece of completed work a shareable shape with a low-friction, non-leading way for the user (or a colleague they hand it to) to surface themselves — if they want to. It surfaces **behaviour** (what was built), never solicits **praise** (whether it was good).

## When NOT to use

- To render a diamond's *state* as a diagram → `/mycelium:diamond-render`. This skill renders *completed work as prose*, not a state machine.
- For an in-progress diamond → this skill refuses (a receipt summarizes finished work; see Rules). Run it after the diamond records `close`.
- For internal retrospective capture → `/mycelium:retrospective`. The receipt is an outward-facing artifact, not a learning log.

## Identifier exposure

**Declared**: YES

### Scope (canvas surfaces touched)

| Canvas file | Identifier-bearing fields | Frequency |
|---|---|---|
| `.claude/canvas/archived-solutions.yml` | `reason` / `notes` prose (may name a tester whose feedback killed a solution) | low |
| `.claude/canvas/opportunities.yml` | `evidence_sources`, `notes` prose | low |
| `.claude/harness/decision-log.md` | decision prose filtered to this diamond (may name contributors) | low–medium |
| `$MYCELIUM_ATTRIBUTION_REGISTRY` env var (canonical) or `.claude/memory/attribution-registry.yml` (fallback) | `people:` block with `name`+`consent`+`note` | read-only consultation; never rendered |

Per `${CLAUDE_PLUGIN_ROOT}/engine/render-conventions.md#hard-rule-consent--privacy-gate`. The registry lives in roadmap-private memory by design — it must never ship in a generated receipt.

### Rationale

The receipt is a **hand-it-over artifact**, so its audience is fixed `external` (stricter than the render fleet's `cohort` default): only `public_ok` renders literal; everything else redacts. A receipt that leaks a tester's name or a private project name to a colleague is a privacy incident, and the user may not notice before sharing — so the gate is conservative by construction, not by operator vigilance.

### Anon-label convention

Per `engine/render-conventions.md#anon-label-convention`:
- Cohort tester → `cohort-tester-N`
- Peer practitioner → `peer-practitioner-N`
- Maintainer / employee → `maintainer-N` / `employee-N`
- Unknown class → `participant-N`

Numbering resets per render; emit an anon-mapping footnote when redaction occurred.

### Consent value semantics (audience `external`)

| Value | Render behavior |
|---|---|
| `public_ok` | Render literal. Append carve-out footnote pointer if entry has non-empty `note:`. |
| `generic_only` | Redact to anon-label (identity is roadmap-private; this artifact is external). |
| `unknown` | Treat as `generic_only` (conservative). |
| (not in registry) | Fail loud unless `--no-identifiers=true`. |

**Project names** are not in the registry; a receipt MUST NOT name a third party's private project. If the source work references a private project name, redact to a generic descriptor and surface a warning. (See the Frida carve-out precedent in `engine/render-conventions.md#carve-out-notes`.)

### Worked examples

**public_ok → literal**: decision-log names `Drew`, registry `{name: "Drew", consent: public_ok}` → renders `Drew` + carve-out footnote pointer.

**generic_only → anon-label**: `archived-solutions.yml#reason` names `Daniel`, registry `{name: "Daniel", consent: generic_only}` → renders `peer-practitioner-1` + anon-mapping footnote.

**not in registry → fail loud**: a receipt source names `Random Name` with no registry entry → fail-loud with three fix options (add to registry, re-run with `--no-identifiers`, edit the source canvas).

### Fixture pointer

- `tests/bash/fixtures/receipt-render/redaction-public-ok-literal.yml`
- `tests/bash/fixtures/receipt-render/redaction-generic-only-anon.yml`
- `tests/bash/fixtures/receipt-render/redaction-no-registry-entry-fail-loud.yml`
- `tests/bash/fixtures/receipt-render/private-project-name-redacted.yml`

## Preflight: Read sources

1. Read `.claude/diamonds/active.yml` (full) to resolve the target diamond.
2. Read `.claude/canvas/archived-solutions.yml`, `.claude/canvas/opportunities.yml`, `.claude/canvas/cycle-history.yml`, and the relevant `.claude/harness/decision-log.md` entries (filtered by `**Diamond**: <id>`). All read-only.
3. Read the attribution registry per `engine/render-conventions.md#registry-path-resolution`. **If absent, STOP: emit no receipt.** Report to the operator: `⚠ no attribution-registry — consent-redaction not enforceable; receipt NOT generated`. Audience here is fixed `external`, which is exactly the case `render-conventions.md` blocks (v0.173.0).
   Until v0.173.0 this step emitted the receipt behind a `do NOT share this receipt externally` header. **That put the artifact in the operator's hands and asked them not to use it** — for a skill whose entire purpose is producing something to hand over, and whose own rationale below says the gate must be "conservative by construction, not by operator vigilance". A header asking someone not to share a shareable artifact IS operator vigilance.
4. Note canvas-state timestamp per `engine/render-conventions.md#canvas-state-timestamp-resolution`.

## Arguments

| Arg | Default | Values | Effect |
|---|---|---|---|
| `--diamond` | `null` | diamond ID | Which completed diamond to render. If omitted and exactly one diamond is in `deliver`/`complete`, use it; else fail loud listing candidates. |
| `--format` | `markdown` | `markdown` \| `json` | Output format. `mermaid`/`ascii`/`markdown-table` are NOT supported (a receipt is prose, not a diagram); fail loud per `engine/render-conventions.md#format-support-negotiation-global-rule`. |
| `--no-identifiers` | `false` | bool | Force all name references to redact regardless of consent state. |

## Workflow

### Step 1: Resolve the diamond
Resolve `--diamond`; apply the single-completed-diamond default; fail loud if zero or ambiguous (list candidates with their phase). If the resolved diamond is not in `deliver`/`complete`, refuse (Rule 2).

### Step 2: Gather the four factual sections (read-only)
- **Problem (as framed):** from the diamond `definition_of_done` (`outcome`/`signal`) and `name`. State the problem the work addressed, in the user's own framing.
- **Assumptions tested:** from `theory_gates_status`, the decision-log entries for this diamond, and any `four_risks` snapshots in `archived-solutions.yml`. List what was checked, not what was concluded about quality.
- **Killed (and why):** read BOTH kill registries — `archived-solutions.yml` entries tied to this diamond (the canonical leaf registry; recorded `reason`) AND `cycle-history.yml` entries with a discard/kill outcome (`terminal_state: killed|archived`, or `outcome: discarded`, or a non-empty `discard_reason`/`discard_phase`). Projects record kills in either place, and a receipt that reads only `archived-solutions.yml` under-reports the work avoided when discards live in `cycle-history.yml` (dogfood finding 2026-06-20, v0.50.0 → v0.50.1). This section is the load-bearing honesty of the receipt — work NOT built is the point — so missing a kill is the costliest omission.
- **Kept / shipped:** surviving `opportunities.yml` solutions + launched entries in `cycle-history.yml`.

### Step 3: Consent check
Run every name-shaped identifier in the gathered prose through the registry per Step 2 of `ost-render` and the table above. Redact private project names to generic descriptors. Audience is `external` — `generic_only` always redacts here.

### Step 4: Emit the receipt (markdown default)

```
# Work receipt — <diamond name>

**What this was.** <problem as framed, from definition_of_done — factual, the user's framing>

**What got tested.** <assumptions checked — behaviour, not a quality verdict>

**What got killed.** <discarded solutions + recorded reason — the work NOT built>

**What got kept.** <surviving solutions / shipped leaves>

---
<footer: see Step 5>
```

**Hard content rule (non-leading + no invented metrics):** report what the USER did. NEVER narrate a tool win. NEVER invent a benefit-metric (a fabricated "N hours saved" / "X% faster" counterfactual is banned — it is unmeasured, it leads the verdict, and it contaminates `/mycelium:framework-health` evidence if it is ever shared back). Use only counts and states that exist in the canvas.

**Format `json`** — same four sections as keyed fields plus `redactions_applied`, for external-system integration. No footer prose; include the origin URL as a field.

### Step 5: Footer (the data flow — see `engine/render-conventions.md` + below)

Append, in order:

1. **Origin line** (for whoever receives it):
   > _Produced with Mycelium, a product-thinking discipline for AI agents. What it is + how this receipt was generated: https://github.com/haabe/mycelium/blob/main/docs/receipts/handoff.md_

2. **Adopter share-back line** (Flow A — only in `markdown`):
   > _Built something with this? If you want, post it here → https://github.com/haabe/mycelium/discussions/new?category=show-and-tell&title=Built%20something%20with%20Mycelium&body=<url-encoded: what were you building, and what did the receipt capture?>_
   >
   > _(Heads up: that opens a public draft you review before posting — this receipt summarizes your own work, so check it first.)_

3. **Lossy-on-export + canonical disclaimer** per `engine/render-conventions.md` (no mermaidchart.com handoff — not a Mermaid format):
   > _Render: `receipt-render` v`<framework-version>`. Source: `.claude/diamonds/active.yml` (+ archived-solutions, opportunities, cycle-history). Canvas state as-of: `<timestamp>`. Format: `<format>`._
   > _Receipt is a static snapshot; canvas remains source of truth. Review before sharing externally._

## Rules

1. **Read-only.** Never modify any canvas or state.
2. **Completed work only.** Refuse on a non-`deliver`/`complete` diamond; a receipt of unfinished work over-claims.
3. **Non-leading + no invented metrics** (Step 4 hard content rule). This is the epistemic core: the receipt exists to surface behaviour without manufacturing the signal it hopes to detect.
4. **Consent gate is non-skippable**, audience fixed `external`. Only override is `--no-identifiers=true`.
5. **Never invent** work, decisions, or outcomes not in the canvas/decision-log.
6. **The tool never posts.** The footer offers deep-links a human chooses to open and submit; the skill transmits nothing (privacy stance, `privacy-assessment` no-telemetry commitment).

## Counter-Argument Check

Before emitting:
1. *"Is any line narrating a tool win or an unmeasured benefit, rather than reporting what the user did?"* If yes, rewrite to behaviour-only (Rule 3).
2. *"Did I run EVERY name-shaped identifier — including ones buried in decision-log prose and kill `reason`s — through the registry, and redact any private project name?"* The leak risk is in prose the user won't re-scan before handing the receipt over.
3. *"Am I rendering a genuinely completed diamond, or dressing up in-progress work as finished?"* (Rule 2.)

## What this skill does NOT do

- Does NOT render diamond state as a diagram → `/mycelium:diamond-render`.
- Does NOT post, send, or transmit anything. It emits a local artifact with volitional share links.
- Does NOT correlate or detect arrivals (no telemetry, no referrer polling). Detection is a human posting to GitHub Discussions of their own accord.
- Does NOT invent benefit-metrics or quality verdicts.

## Test fixtures (G-V12 / Check 43)

Check 43 (`tests/validate-template.sh`) enforces the `identifier_exposure` frontmatter + `## Identifier exposure` body section on this `-render` skill. Functional redaction fixtures per the Fixture pointer list above.

## Theory citations

- Torres (assumption-testing shape; surface behaviour not opinion)
- Moore, *Crossing the Chasm* (the spontaneous onward-handoff is the load-bearing adoption signal the data flow instruments)
- Cavoukian / Privacy by Design (no-telemetry, local-only generation, volitional share)
- WCAG 2.1 AA (n/a — prose artifact, no diagram palette)
