---
name: render
description: Central dispatcher for the canvas/state render fleet. Routes intent to a specialist (`/mycelium:diamond-render`, `/mycelium:ost-render`, `/mycelium:cycle-render`) OR lists what's renderable. Cross-cutting views spanning multiple canvases (opp→sol→cycle traceability, confidence-over-time, cluster-graduation-flow) are research-gated and NOT emitted by default. See `${CLAUDE_PLUGIN_ROOT}/engine/render-conventions.md` for shared conventions.
metadata:
  instruction_budget: "60"
  framework_dependency: "mycelium"
  framework_dependency_note: "Routes to specialist render skills. Consults the attribution registry only if a cross-cutting view activates a YES-exposure canvas."
  identifier_exposure: "MIXED"
---

# Render Dispatcher

Central entry point + menu for the canvas/state render fleet. Routes intent to specialists or surfaces what's available. Cross-cutting views are research-gated and NOT emitted by default. Completes the v0.40.0-announced render fleet foundation.

## When to use

- "Show me the OST" / "render the diamond state" / "visualize the cycles" → dispatcher recommends + routes to the specialist (recommend, do NOT auto-invoke).
- "Visualize how opportunity X became cycle Y" → cross-cutting traceability intent. Dispatcher surfaces that the view is research-gated; does not emit a default rendering.
- Discovery: "what renderable views does Mycelium have?" → dispatcher lists specialists + their states.

## When NOT to use

- If the user names a specialist directly (`/mycelium:diamond-render`, `/mycelium:ost-render`, `/mycelium:cycle-render`), the specialist is the one-hop path. Do NOT re-route through the dispatcher.
- For cross-cutting views that already have dedicated skills (e.g., `/mycelium:framework-health` is its own audit; not a render specialist).

## Identifier exposure

**Declared**: MIXED

### Scope (per-canvas table — REQUIRED for MIXED)

| Canvas | Exposure | Identifier-bearing fields | Activated when |
|---|---|---|---|
| `.claude/canvas/opportunities.yml` | YES | `evidence_sources`, `notes` | `--view traceability` (deferred), `--view ost-summary` |
| `.claude/canvas/cycle-history.yml` | YES | `learnings.process` prose, `related_corrections` | `--view traceability` (deferred), `--view cycle-summary` |
| `.claude/canvas/archived-solutions.yml` | YES | `discard_notes` prose | `--view traceability` (deferred), `--view discards` |
| `.claude/canvas/landscape.yml` | YES (low) | `notes`, `evidence_sources` | `--view competitive-landscape` (deferred) |
| `.claude/diamonds/active.yml` | NONE | none | any view including the diamond |

### Rationale

Dispatcher behavior depends on which cross-cutting view is invoked. MIXED with per-canvas scoping is the only honest declaration: YES would force registry consultation on diamond-only views (unnecessary cost); NONE would silently leak identifiers on traceability views (incident). Each cross-cutting view's implementation MUST consult the registry per `engine/render-conventions.md#hard-rule-consent--privacy-gate` for the YES-exposure canvases it activates and skip the consultation only for NONE-exposure canvases.

For v0.40.3 ship: the dispatcher ships WITHOUT cross-cutting views. All MIXED-relevant identifier surfaces are inactive. The MIXED declaration is forward-looking — it names the canvases that WILL activate when cross-cutting views land in subsequent patches per the research-first methodology.

### Anon-label convention

Per `engine/render-conventions.md#anon-label-convention`. Numbering shared across a single dispatcher invocation regardless of canvas count (`cohort-tester-2` in cycle-003 IS `cohort-tester-2` in opp-004 evidence).

### Consent value semantics

Per `engine/render-conventions.md#consent-value-semantics`.

### Worked examples (forward-looking)

**`--view traceability` (deferred)**: activates opportunities.yml + cycle-history.yml + archived-solutions.yml. Registry consultation runs. Multi-canvas anon-label numbering shared.

**`--view diamond-only` (always available — alias for routing to diamond-render)**: touches only active.yml. Registry consultation SKIPPED per the per-canvas exposure table. No anon labels emitted.

### Fixture pointer

- `tests/bash/fixtures/render/dispatcher-recommend-not-invoke.yml` (routes to specialist)
- `tests/bash/fixtures/render/dispatcher-list-options.yml` (discovery mode)
- `tests/bash/fixtures/render/dispatcher-view-traceability-mixed-consent.yml` (deferred — fires once traceability view ships)
- `tests/bash/fixtures/render/dispatcher-view-diamond-only-no-redaction.yml` (alias-to-specialist behavior)
- `tests/bash/fixtures/render/dispatcher-view-traceability-no-registry-entry.yml` (deferred — fail-loud on missing identifier)

## Arguments

| Arg | Default | Values | Effect |
|---|---|---|---|
| `--list` | `false` | bool | Print the dispatch table + deferred cross-cutting views, do not route |
| `--view` | `null` | `traceability` \| `confidence-trajectory` \| `cluster-graduation-flow` \| `canvas-dependency-graph` | Cross-cutting view selector (all currently deferred per research-first methodology) |
| `--format` | `mermaid` | `mermaid` \| `ascii` \| `json` | Format hint for routed specialists (overridable per specialist) |
| `--theme` | `base` | `base` \| `dark` | Theme hint for routed specialists (`dark` opt-in for WCAG-by-construction per `engine/render-conventions.md#wcag-aa-theme-convention`) |

## Workflow

### Step 1: Parse intent

Identify whether the request maps to:
- A single canvas → route to specialist (Step 2)
- A cross-cutting view → surface the deferral (Step 3)
- Discovery / `--list` → enumerate options (Step 4)

### Step 2: Route to specialist

Map canvas to specialist. **Recommend, do NOT auto-invoke** (architecture decision Q1):

| Canvas / intent | Specialist | Beta risk |
|---|---|---|
| opportunities.yml | `/mycelium:ost-render` | none |
| diamonds/active.yml | `/mycelium:diamond-render` | none |
| cycle-history.yml | `/mycelium:cycle-render` | none |
| landscape.yml | `/mycelium:landscape-render` (deferred) | `wardley-beta` |
| bvssh-health.yml | `/mycelium:bvssh-render` (deferred) | `radar` beta |
| dora-metrics.yml | `/mycelium:dora-render` (deferred) | `xychart-beta` |
| scenarios.yml | `/mycelium:scenarios-render` (deferred) | none |

Output shape for routing:

```
> Recommend: `/mycelium:ost-render` (--format <inherited>, --theme <inherited>)
> The canvas remains source of truth; this render is a snapshot.
```

Specialist not yet shipped → surface deferral + promotion-trigger.

### Step 3: Cross-cutting view (currently all deferred)

Each `--view` value names a candidate view; all are research-gated:

| View | Spans canvases | Status | Promotion trigger |
|---|---|---|---|
| `traceability` | opportunities + cycle-history + archived-solutions | DEFERRED | Research-first methodology converges on a candidate shape; founder visual eval ≥4.0 |
| `confidence-trajectory` | diamonds/active.yml history + decision-log | DEFERRED | Cohort tester asks for confidence-over-time visualization |
| `cluster-graduation-flow` | corrections.md + cluster-instances.md | DEFERRED | External receipts-case need for graduation-flow visualization |
| `canvas-dependency-graph` | every canvas's `cross_ref` + `dependencies` | DEFERRED | Canvas-health drift incident traces to cross-canvas dependency staleness |

Output shape for deferred-view requests:

```
> ⓘ View `traceability` is deferred.
> The shape requires research-first methodology + founder visual eval
> before a default rendering can ship. The framework intentionally does
> NOT emit a "best guess" view to avoid teaching users to think with a
> shape that wasn't validated.
>
> Promotion trigger: <named in table>
```

### Step 4: List options (discovery mode)

Print the Step 2 dispatch table + Step 3 deferred view list. Each entry names: skill or view, what it renders, supported formats, beta risk, current status (shipped / deferred-with-trigger).

## Rules

1. **Read `engine/render-conventions.md`** before any emit.
2. **Never modify canvas state.** Renders are read-only by class.
3. **Apply canonical disclaimer + lossy-on-export template** per the engine doc (when routing, the user emits the render via the specialist; when listing options, no disclaimer needed).
4. **Routing: NEVER silently sub-invoke.** Name the recommended specialist + arg-set explicitly. User retains one-hop control.
5. **Deferred views: NEVER emit a "best guess" rendering.** The trap is exactly "ship a looks-reasonable-to-me view"; the dispatcher's job is to gate against it.
6. **Format/theme hints route through:** when recommending a specialist, pass `--format <inherited>` and `--theme <inherited>` so the user's invocation matches dispatcher intent.

## Counter-Argument Check

Before emitting:

1. *"Is this render conveying current state, or a stale snapshot the canvas no longer matches?"* Each routed specialist runs its own staleness check (per `engine/render-conventions.md#staleness-check-distinction`); dispatcher does not pre-emptively check (the specialist owns it).
2. *"Am I about to silently auto-invoke a specialist instead of recommending?"* The architecture decision is load-bearing — silent sub-invocation defeats the dispatcher's reason to exist beyond menu-discovery. If routing logic ever becomes "if intent matches X, just emit X's output," surface the regression and stop.
3. *"Am I about to emit a 'best guess' cross-cutting view?"* If `--view <name>` is set and the named view's status is deferred, the only correct output is the deferral message. NEVER fall through to a default rendering.

## What this skill does NOT do

- Does NOT emit single-canvas renders directly. That's the specialists.
- Does NOT modify canvas state. Read-only by class.
- Does NOT auto-invoke specialists. Recommends + names the user-facing invocation.
- Does NOT emit cross-cutting views until the research-first methodology converges + manual visual eval lands. The deferral is the feature.

## Theory citations

- Hick's Law (single recommended specialist; deferred-view fail-loud avoids decision-tax)
- Argyris triple-loop (the dispatcher routes between loops; doesn't claim to BE a loop)
- Counter-Goodhart (never emit a "best guess" cross-cutting view; the deferral IS the discipline)
