# harness-review.md — verifying a generated/updated harness (force-load)

The verification criteria for a project harness. Used by **migration's REVIEW phase** and by
**`go`'s final-review lenses 3–4** — one source of truth, so both judge the harness the same way.
The spec being verified against is `harness-format.md`.

This is an **adversarial pass**: the reviewer's job is to find holes, not to bless the work
(self-judgment is the weak move). The four dimensions below are *what to
check*, applied with judgment — not a box-ticking checklist that earns a pass by being walked.

## Dimension 1 — content (does each file substantively meet its spec?)

For each file, check it against `harness-format.md`'s spec for that file, then against the
cross-cutting quality bar:

- **Meets its own spec** — has the *kinds* of information harness-format requires for that file, at
  that file's altitude, and clears that file's quality floor (e.g. business-rules: every rule
  verifiable, each "must" paired with a "must not," edges concretely disposed; security: failure
  paths named, explicit "not allowed" stated; standards: every rule has a violation criterion).
- **Five principles** — non-derivability (nothing the code already reveals), work-changing (would
  change the next agent's work), density (every sentence carries a fact), project-specificity (no
  universal truths), consequence-of-absence (removing it would break something).
- **Four techniques** — verifiable statements, counter-cases stated, mechanism described (not just
  outcome), edge cases concrete (no "handled appropriately").
- **Language** — the harness is written natively in the **language the user communicates in**
  (language-agnostic; the specific language is discovered, not assumed). A harness that doesn't match
  the user's language is a defect. (The reviewer is told the user's language by the orchestrator at
  dispatch — in both migration and go the finished work is verified by an independent dispatched
  reviewer, never self-reviewed.)
- **Harness describes the project only (blocking)** — flag any file that describes itself (its state,
  thinness, lifecycle, or *its own purpose / how to read it* — e.g. "read this instead of the code"),
  its origin (that it was generated / migrated / is a first-cycle artifact; status.md listing the
  documentation layer itself as a delivered capability), or that uses the **generating tool's name or
  dryforge's coined vocabulary to label the doc system** ("dryforge" anywhere; calling the docs "the
  harness"/"하네스", a section "Harness navigation", or naming "3-doc"/"delta"/"wave"). Section titles
  use the project's plain terms. It describes the project, not the document. ("dryforge" is a reliable
  sweep; for "harness" use judgment — a project's own *test* harness is legitimate, labeling the doc
  layer a harness is not.)
- **Entry-point navigation is one whole-harness tree** — CLAUDE.md/AGENTS.md show the navigation as a
  single project-root directory tree (`├──`/`└──`) covering the entry files + `docs/` + module
  `AGENTS.md` at their dirs; flag a table, a flat list, or a docs-only tree with modules tacked on.
- **No baked scope-freeze in any doc** — flag *any* doc that writes planned-but-unbuilt scope (a
  status.md "remaining" item) as a permanent constraint: a hard gate or standards rule saying "don't
  build X yet", a business-rule calling a planned capability "impossible by construction", or a "keep
  shape Y" forward-compat gate where a remaining item will change shape Y. Planned scope is a *status*,
  not a permanent invariant — it falsely conflicts with the cycle that builds it. Describe the current
  state, not a permanent ban; hard gates and domain laws are permanent only.

The failure mode to hunt: a **hollow shell** — structurally present, substantively empty. A file
that reads as generic boilerplate, restates what code shows, or fills a section with modifiers
("modern," "robust," "appropriate") fails this dimension even though the section "exists."

## Dimension 2 — format (self-containment)

- **No cross-references between `docs/` files** — no "see architecture.md"; each file states what it
  needs at its own altitude.
- **Each file at one altitude** — no upper-altitude detail replicated below, no lower-altitude
  implementation mentioned above. The same topic appearing in two files is fine *only* if each
  treats it at its own altitude.
- **No 3-doc references** — nothing points at `.dryforge/` (the 3-doc is archived after the task;
  the pointer would dangle).
- **No constraint-ID labels (blocking).** Flag any constraint-ID carried into the harness — the
  3-doc's `INV-N` / `T-N`, or any `XXX-N` scheme — and any reference to another doc's invariant/rule
  *by label*. These dangle once the 3-doc is archived and violate self-containment; invariants must be
  stated **by content**. A sweep for `\b[A-Z]{2,}-[0-9]+\b` across the harness catches most.
- **Module AGENTS.md** references no other module AGENTS.md and no `docs/` file.

## Dimension 3 — completeness (required files present)

- All `docs/` files exist (the 7 core + tracking: status.md, decisions/index.md, findings.md).
- CLAUDE.md and AGENTS.md both exist, with **identical content**.
- An AGENTS.md exists for every identified module (module-identification heuristic in
  harness-format.md). A missing module AGENTS.md for a real module is a defect.
- An empty file is correct only when its category genuinely doesn't apply; an empty file for an
  applicable category is a defect (hollow shell), caught by Dimension 1.

## Dimension 4 — against the source (omission vs hallucination)

Cross-check the harness against the code, **both directions**:

- **Omission** — an intent / constraint / mechanism that the code **cannot derive on its own** is
  missing from the docs. This is the real omission. *Code-derivable facts being absent is not an
  omission* — by the non-derivability principle, the harness deliberately omits them.
- **Hallucination** — the docs assert something the code does not contain. Flag it — **except**
  content that legitimately derives from **future scope**: status.md's "remaining" items,
  business-rules' not-yet-implemented rules, and other forward-looking content sourced from the
  Foundation/design. For those, code absence is *normal*, not a hallucination. Distinguish "the doc
  describes a planned future state" (correct) from "the doc describes a present state the code
  contradicts" (a real hallucination).

## Findings → disposition

Each finding is one of:
- **Internally resolvable** (a hollow section you can deepen from sources already in hand, a
  cross-reference to inline, an altitude violation to move) → fix it directly.
- **Needs user intent** (a gap only the user can fill — a domain rule, a policy decision, a
  rationale not on the record) → do not invent it; raise it to the user (migration: ask in the user
  gate; go: surface as a blocking finding the orchestrator escalates).

In `go`'s final review, harness findings carry the same blocking/advisory split as code findings.

## Universality guard

Stack-agnostic. The criteria judge information *kind*, density, and altitude — never conformance to
a particular stack. What counts as a module, a contract, or a representative flow is whatever the
project actually is, discovered at runtime.
