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
3. **Rank, take top-N for the mode, filter ineligible candidates** (utility
   modules, anything failing `spec-contract.md`'s "when NOT to write a spec").
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

## Fallback tier (test-independent — when the primary pool yields fewer than N)

Many perfectly real repos have few or no tests — a plain script repo, a young
frontend, an ML notebook tree, a CLI, an agent/plugin repo of Markdown skills. An
empty hotspot pool there is a false negative, not a true "nothing to document."
When the primary pool yields **fewer than N** candidates for the mode, widen the
inputs (never lower the bar to noise) and fill the remaining slots from a fallback
pool — modules with `LOC > 100` that the primary tier missed *only* for lack of
tests — ranked by a **test-independent importance score** built from evidence the
repo actually contains:

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

> No modules above the hotspot threshold detected. Run `/archcore:capture <path>`
> on demand when you identify a module worth documenting.

## Top-N by mode

| Mode | N candidates |
|---|---|
| small | 3 |
| medium | 5 |
| large (per selected domain) | 3 |

If the combined pool (primary + fallback) has fewer than N modules, list all.

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

> Detected N sibling files matching `<pattern>`. Run `/archcore:decide` to codify
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

> To capture any of these, run `/archcore:capture <path>` for modules,
> `/archcore:decide` for decisions, `/archcore:decide` for rules.

Do NOT auto-invoke those skills — let the user walk through on their own pace.

## Per-domain scoping (large mode)

When invoked from large mode's per-domain pass, the candidate pool (both tiers) is
restricted to files under the selected domain's path. The top-N is 3 per domain.
The rationale lines prefix the candidate path with the domain tag:

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
> `/archcore:capture` on these if the top-N list feels incomplete.

These concrete signals and filename patterns are **non-exhaustive examples** to
orient ranking — absence from a list is NOT absence of signal; fall back to the
importance method above for anything not shown.
