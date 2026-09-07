# Hotspot Ranking

Selects the small set of source modules most worth capturing as `spec` documents
in `/archcore:init` (Tier-2), and as `spec` / `adr` / `rule` candidates elsewhere.

## What it detects

A HOTSPOT is a module where the project's load-bearing logic concentrates and on
which the rest of the system most depends — the few files whose contract is most
worth pinning down on day one. "Most worth documenting" is a function of evidence
the repo actually contains: how much logic lives in the file, how much the team
invested in testing it, how many other modules depend on it, and how actively it
changes. The concept is language- and domain-agnostic: it holds for a web service,
an ML pipeline, an embedded driver, a game system, a data/IaC module, a CLI tool,
a plain script repo, or the instruction files of an agent / markdown tooling repo.
Tests are the single strongest signal **where they exist** — but their ABSENCE is
not absence of importance, so ranking degrades gracefully to test-independent
signals rather than returning an empty pool.

## How to find it (any codebase)

1. **Enumerate candidate modules** per `detect-modules.md` (after its exclusions,
   and honoring its narrow instruction-modules exception for plugin/markdown
   tooling repos). For each, gather the signals you can cheaply read: source
   `LOC`, companion `test_LOC`, **fan-in** (how many *other* modules import or
   reference it), **public surface** (the count/shape of symbols it exposes to the
   rest of the system), and — when `git` is available — recent churn.
2. **Build the pool in two tiers, primary first.** The primary tier is
   high-precision and tests-aware; the fallback tier fills remaining slots when the
   primary tier is short, using test-independent signals. Definitions below.
3. **Rank, filter ineligible candidates** (utility modules, anything failing
   `spec-contract.md`'s "when NOT to write a spec"), then take the depth's budget
   from what survives ("Spec budget by coverage rate" below).
4. Emit a signal only on positive evidence; when no candidate is unambiguous,
   prefer omission over a guess — never invent.

## Primary tier (tests-aware — high precision)

For each source module:

```
score = LOC + 0.7 * companion_test_LOC
```

`LOC` is the source file's line count; `companion_test_LOC` is the summed LOC of
its test partners (per `detect-modules.md` "Test-LOC companion lookup"). The 0.7
weight reflects that heavily-tested code is important *and* its tests amplify its
LOC, but the source file itself is the primary artifact — don't let a 2000-line
test suite out-rank a 400-line critical module with 600 LOC of tests.

A module enters the **primary pool** only if BOTH:

- `LOC > 100`, AND
- EITHER `companion_test_LOC > 50` OR `LOC > 200`.

Rationale: either the file is substantial on its own, or the team invested ≥ 50
LOC in testing it — that investment signals the contract matters.

## Fallback tier (test-independent — when the primary tier fills fewer slots than the budget)

Many perfectly real repos have few or no tests — a plain script repo, a young
frontend, an ML notebook tree, a CLI, an agent/plugin repo of Markdown skills. An
empty hotspot pool there is a false negative, not a true "nothing to document."
When the primary tier fills **fewer slots than the depth's budget** ("Spec budget by
coverage rate" below), widen the inputs (never lower the bar to noise) and fill the
remaining slots from a fallback pool — modules with `LOC > 100` that the primary tier
missed *only* for lack of tests — ranked by a **test-independent importance score**
built from evidence the repo actually contains:

1. **Fan-in / centrality (primary signal)** — how many *other* source modules
   import or reference this one through the repo's own mechanism: a language
   import / package path, or — for an instruction/tooling repo — an explicit
   cross-reference (a `[[link]]`, a relative path mention, a shared include). A
   module many others depend on is load-bearing. Discount a barrel/index file that
   only re-exports and carries no logic of its own (high fan-in, zero contract).
2. **Concentrated public surface** — a focused, named public interface (a small
   set of exported/public symbols, a declared API, a command/handler the rest of
   the system calls) over substantial internals. Prefer a 150-LOC module exposing
   4 public entry points over a 150-LOC leaf that exposes none.
3. **Size** — `LOC` as a proxy for how much contract lives there; among
   test-less modules, the larger ones carry more.
4. **Churn** — the git-activity bonus below, when `git` is available.

Combine as: rank by what others rely on (fan-in and concentrated surface), with
size and churn as amplifiers; break ties by path for determinism. A pure leaf that
nobody imports and that exposes nothing stays out — it has neither dependents nor a
contract worth a spec. Mark fallback-tier candidates in the stub line (e.g.
`no tests — central: imported by 9`) so the user sees why it qualified.

If, after BOTH tiers, the pool is still empty (no module clears `LOC > 100` at
all), skip the hotspot step and surface in the closing message:

> No modules above the hotspot threshold detected. Run `/archcore:document <path>`
> on demand when you identify a module worth documenting.

## Spec budget by coverage rate

Day-one init sizes the number of **full specs** from the repo's own evidence, never
from a constant. The budget is a share of the ranked candidate pool:

```
budget = max(floor(depth), round(rate(depth) × pool_size))
budget = min(budget, pool_size)
```

| Depth | `rate` (share of pool) | `floor` (sparse-repo minimum) |
|---|---|---|
| `light` (opt-down) | 0.10 | 3 |
| `standard` (default) | 0.25 | 4 |
| `deep` (opt-up) | 0.60 | 6 |

`pool_size` is the count of ranked candidates **after** eligibility filtering — primary
tier plus fallback tier, with utility modules and anything failing `spec-contract.md`'s
"when NOT to write a spec" already removed. Slots fill primary-tier-first by score, then
from the fallback tier by its own score, exactly as before; the two tiers change which
candidate takes a slot, never how many slots exist.

**The budget carries no absolute maximum.** A pool of 214 load-bearing modules budgets
54 specs at `standard`; a pool of 12 budgets 4. Scale (`small` / `medium` / `large`) no
longer sets the spec count — it still sets the other artifacts (top-level map, domain
dialog, cross-cutting scan). What bounds the count is the pool, and the pool is
quality-gated: a module enters it only through the primary-tier thresholds above or the
fallback tier's fan-in / public-surface evidence, so a repo with few load-bearing
modules cannot produce a large budget however deep the run.

Change: this replaces the flat `small` / `medium` rows (3/4/6, 4/6/10) and large mode's
`clamp(rate × selected_domain_count, min, max)` with one formula for every scale. The
clamp's constant maximum (12 / 24 / 40) is what kept a 773-module repo at 24 specs while
a 40-module repo took the same ceiling — the same thinness `magic-first-day-init.adr`
already corrected once at the flat-cap layer.

**Per-selected-domain floor (large mode).** Every domain selected in `SKILL.md` Step A.0
gets a floor of ≥ 1 spec, so no domain the user named ends with zero. Remaining slots up
to the budget fill by **repo-wide** rank across ALL domains, selected or not — an
unselected domain's hotspot still places when it outranks a selected domain's weaker
one. On `skip` (no domain selected) the whole budget fills by repo-wide rank alone.

**`--domain=<slug>` re-run.** Apply the same formula to the **narrowed** pool — eligible
candidates under that domain's tree only. A re-run therefore tops up a domain in
proportion to what that domain holds, at the same rate and floor as a day-one run.

**Ceiling, never a quota.** IF the pool holds fewer candidates than the computed budget,
THEN take every candidate and stop; never pad to hit a number. A sparse repo at `deep`
yields the same as at `light`.

`/archcore:init`'s Detect phase (`SKILL.md` Step A.3) collects signal data for the
**whole eligible pool** — path, LOC, companion-test LOC, fan-in, churn — because
`pool_size` is an input to every depth's budget and a `depth:` toggle in the preview
(Phase C/D) must re-slice without re-reading. Signal collection reads no source files;
only *synthesis* (which candidates get a full spec body) is gated by the active depth.

The ranked hotspots beyond the budget are NOT dropped — they are recorded in the
architecture-overview register (`compose-overview.md` Part 3) as `→ /archcore:document`
rows, so the full map of load-bearing modules stays visible at ~0 token cost while only
the budgeted candidates pay for synthesis.

## Flagship specs (size/churn-gated: decomposition eligibility)

A hotspot module that clears EITHER `LOC > 3000` OR falls in the **top quartile of
churn** among the ranked candidate pool (its `commits_last_90_days` score, from the
git-activity bonus below, ranks in the top 25% of candidates that have git history)
is a **flagship** candidate. Flagship status buys one thing: `SKILL.md` Phase E may
decompose the module instead of composing it as one spec.

- **Default — one spec.** Compose under `_shared/spec-contract.md`'s ≤ 120-line cap,
  the same cap every other spec is measured against. Flagship status no longer raises
  a cap: the contract carries one number for every path, so there is nothing left to
  raise.
- **Decomposition — only with genuine separable sub-contracts.** When the module
  exposes ≥ 2 independently-consumable sub-surfaces with distinct external consumers
  (e.g. a 6000-LOC service with a read/query surface and a separate command/mutation
  surface) — split into **≤ 3 sub-specs**, one per sub-surface, each inside the same
  ≤ 120-line cap: `filename=<module-slug>-<sub-surface-slug>`,
  `directory=<domain-or-'architecture'>`. Relate the sub-specs to each other
  (`related`) in addition to the standard overview edge.

**Never split to pad.** A large or hot file with one cohesive contract (no separable
sub-surface) stays a single spec — "prefer omission over a guess" governs the split
decision exactly as it governs candidate selection in the first place: when the
sub-surface boundary is not unambiguous, do not split. A body that then runs past the
cap follows `_shared/spec-contract.md` "Over the cap", whose rule 5 reaches the same
answer and whose rule 6 makes the excess visible in the closing report.

Flagship status does not change the hotspot's rank or its consumption of the depth's
spec budget ("Spec budget by coverage rate" above) — a decomposed flagship still
occupies exactly **one** slot in that budget; its ≤ 3 sub-specs share that one slot,
so the flagship gate never inflates the computed budget.

## Suggested doc type (heuristic)

Pick the most likely archcore type per candidate. This is a hint for the user; they
can override.

**In `/archcore:init` (Tier-2):** every hotspot artifact is composed as a `spec`
regardless of the hint below — the hint is used only to *filter out* ineligible
candidates (e.g. a `utils`/`helpers` module, or one that fails `spec-contract.md`'s
"when NOT to write a spec"). init surfaces survivors as spec **stubs** in its single
preview and composes/creates the bodies only after `confirm`; it does not emit the
standalone propose list described under "Presentation" below.

| Heuristic | Suggestion |
|---|---|
| `test_ratio > 1.5` (i.e. tests outweigh source) | `spec` — heavily tested contract |
| File contains ≤ 5 exported public symbols, ≥ 100 LOC | `spec` — concentrated public surface |
| Filename contains `config`, `policy`, `strategy`, `options` | `adr` — decision surface |
| Filename contains `middleware`, `adapter`, `handler`, `wrapper`, and ≥ 3 siblings share the suffix | `task-type` — repeating extension pattern |
| Filename contains `utils`, `helpers`, `common` | (suppress — utility modules rarely warrant a spec) |
| Default | `spec` |

The `task-type` suggestion also flags a potential sibling pattern — when ≥ 3
siblings share the suffix, add a separate line to the closing message:

> Detected N sibling files matching `<pattern>`. Run `/archcore:document` to codify
> the shape as a `task-type` doc for future additions.

## One-line rationale template per candidate

```
<relative-path> — <LOC> LOC source, <companion_test_LOC> LOC tests. Suggested: <doc-type>. <short reason>.
```

Where "short reason" is:

- For `spec` by test-ratio: `heavily tested (<ratio>:1)`.
- For `spec` by symbol count: `small public surface, substantial internals`.
- For a **fallback-tier** candidate: `no tests — central (imported by <fan-in>)` or `no tests — <LOC> LOC, public surface`.
- For `adr`: `filename suggests decision surface`.
- For `task-type`: `sibling pattern with <count> peers`.

## Presentation

Show candidates as a numbered list. At the end, a single hint:

> To capture any of these, run `/archcore:document <path>` for modules, and
> `/archcore:document` for decisions and rules.

Do NOT auto-invoke those skills — let the user walk through on their own pace.

## Day-one per-domain floor vs. `--domain` re-run scoping

Two different mechanisms apply "per domain," at two different times — do not
conflate them:

- **Day-one large-mode dialog (Step A.0).** The candidate pool is still ranked
  **repo-wide** (not restricted to any one domain's file tree), and the budget comes
  from the repo-wide `pool_size`. What the selection changes is *allocation*: each
  selected domain is guaranteed a floor of ≥ 1 spec, with the rest of the budget
  filled by repo-wide rank. This is a **budget allocation**, not a
  candidate-pool restriction, and it also drives how many domains get a data-model
  doc (data-model breadth is decoupled from the dialog entirely — see
  `detect-data-model.md`).
- **A later `/archcore:init --domain=<slug>` re-run.** This restricts the
  **candidate pool itself** to files under the one named domain's path, then applies
  the same `rate` / `floor` formula to that narrowed pool. A dense domain therefore
  tops up with more specs than a thin one, instead of both receiving one flat number.

The rationale lines for a `--domain` re-run prefix the candidate path with the domain
tag:

```
[domain:billing] apps/billing/src/invoice-calculator.ts — 312 LOC source, 540 LOC tests. Suggested: spec. heavily tested (1.7:1).
```

## Git-activity bonus (optional)

If `git` is available, add to BOTH tiers' scores:

```
score += 0.3 * commits_last_90_days
```

Where `commits_last_90_days` is:

```
git log --since=90.days --oneline -- <file> | wc -l
```

This biases ranking toward files under active change, which tend to be where
context gaps hurt most. Gracefully skip when `git` is unavailable or repo is
shallow.

## Stability

Ranking is a ranked list, not a hard boundary — a file with score 260 ranked #4 is
very similar to one at #3. When the candidate pool has many near-ties at the
cutoff, the closing message can nudge:

> Other candidates just below the cutoff: <path-1>, <path-2>. Consider
> `/archcore:document` on these if the budgeted list feels incomplete.

These concrete signals and filename patterns are **non-exhaustive examples** to
orient ranking — absence from a list is NOT absence of signal; fall back to the
importance method above for anything not shown.
