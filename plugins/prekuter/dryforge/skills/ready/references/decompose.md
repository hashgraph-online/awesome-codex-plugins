# decompose.md — DECOMPOSE (deconstruct the INPUT into ELICIT material)

DECOMPOSE takes the raw INPUT (and the code/harness context ORIENT loaded) and breaks its
*content* into material ELICIT can use. This stage **classifies, organizes, and flags — it does not
judge.** "What is correct?" (conflict) and "is it enough?" (gap) are deferred: conflicts go to
ELICIT as questions, gaps are uncomputable until ELICIT establishes the depth floor (first cycle: the foundation design's character→depth; delta: the harness).

**Do not refine the input in place.** The moment you polish the INPUT as a draft, it hardens into
ground truth — that is authority creep, the exact failure `ready` exists to prevent. The INPUT is
**ore to mine, not a draft to polish**. So this stage's output is *signal* (the raw classified
material), and the spec is written fresh from the *validated intent* ELICIT produces (`elicitation.md`),
not from the INPUT itself.

**Floor, not ceiling.** The axes and rules below are the floor; how you read each INPUT fragment is
your judgment. Classification and mechanical translation are in scope (see "What 'don't judge'
means"); conflict-resolution and gap-scoring are not.

## Classify each fragment → its destination

| INPUT content | → |
|---|---|
| domain / behavior | EXTRACT track → spec behavior + foundation domain |
| technical | PRESENT track → foundation technical decisions + spec API |
| work objective / scope | spec objective / scope |
| invariants / hard constraints | spec invariants + handoff hard gates |
| non-derivable form (wire format, a specific predicate, a data structure) | **preserve** (code/data block) |
| implementation code · task-order/dependency graph · noise | **discard** |

**Classification is not partition — file under every axis a fragment informs.** Much real content is
dual-natured: a technical choice carries a *domain consequence* (e.g. "eventual consistency" is
technical, but it triggers the domain question "during the inconsistency window, how does X behave?");
an invariant ("an order's total = sum of line items") is both an *invariant* (handoff hard gate) and a
*behavior rule*. **File it under each axis it informs; when unsure which axis owns it, duplicate rather
than choose.** Mis-filing hides a gap (the owning axis shows no coverage); over-filing costs only an
extra sweep. (Keep-biased default, applied to classification.)

## Discard what is derivable or noise

- **Implementation code** — the agent can re-author it after reading the project, so it is not
  intent. Discard the code itself (but see the conversion below — its *behavioral* content is kept).
- **Task-order / dependency graph** — PLAN recomputes this from the whole project. Trusting an
  INPUT-supplied graph would bypass the producer's core computation — so discard it here.
- **Pure noise** — but use a *test*, not a vibe: noise = **removing it changes nothing a downstream
  agent must honor.** If a line states or constrains behavior, an invariant, a boundary, or a scope
  edge — even tersely, even as a *repeat* — it is **signal, not noise.** **Repetition is an importance
  signal, not redundancy:** a user who restates "it must never lose a write" is *emphasizing* a
  load-bearing constraint, not padding. (And when you dedup wording below, preserve the constraint —
  don't let the merge erase the emphasis that flagged it.)

## Preserve non-derivable forms verbatim

A wire format, a specific predicate, a concrete data structure — anything independent judgment could
get **wrong versus the designer's intent** — is preserved **verbatim as a code/data block**. If you
discard it, a later independent decision that diverges from intent cannot be recovered.

## Premature code → behavioral contract

Premature implementation code is **converted** to a behavioral contract, not kept as code and not
silently dropped: *"write this code"* → *"for input X produce output Y; hold this invariant."* The
keep/cut line is precise:

| In the INPUT | Do |
|---|---|
| implementation code blocks (source, queries, schema/DSL, ...) | convert to a behavioral contract — **delete the code only after** lifting its behavior (see below) |
| feature scope, invariants, API surface, design intent | **keep** — things independent judgment could get wrong |
| non-obvious shapes (wire format, a specific predicate, a data structure) | **keep as a code/data block** — not derivable, must be pinned |

**The keep/cut line:** cut what reading the project reveals; keep what independent judgment could get
wrong versus the designer's intent. This conversion is **classification + mechanical translation**,
not conflict mediation — the keep/cut decision *is* a classification judgment and belongs here.

**Keep-biased gray-zone default (the cost is asymmetric — borrow `output-format.md`'s thinking-base
rule).** A wrongly-*dropped* invariant is **unrecoverable** (the source is gone, see below); a
wrongly-*kept* block is **cheap** (ELICIT/SPEC demotes it later). So the tie-breaker is **not**
symmetric: **unsure whether a fresh agent could re-derive it from the project? Preserve it.** Code
encodes load-bearing nuance that prose misses — a rounding direction, a `<` vs `<=` boundary, an
ordering tie-break, a null branch, a field order. When converting code to a contract, if the code
carries *any* such edge the contract restatement might not fully capture, **keep the original snippet
verbatim as a code/data block *alongside* the contract** — the two are not exclusive, and pairing them
costs little while giving ELICIT both the question material and the ground truth to check it against.
**Nothing downstream can recover what you cut here** — no later stage (REVIEW(A), the 3-doc-gate) ever
sees the raw INPUT again, so a dropped nuance is gone for good.

## Dedup, but never merge a difference

- **Same fact from several sources → merge into one** (remove the redundancy).
- **Sources that say it *differently* → do NOT merge.** A difference is a conflict — flag it (below),
  never average it away.

## Flag every source difference as a question candidate — don't resolve it

When sources disagree — INPUT↔code, INPUT↔harness, code↔harness, an attached doc↔a spoken
description, anything — **do not pick one yourself. Flag it as an ELICIT question candidate.** The
question takes the form *"the situation is X — which is right?"* or *"I consolidated it this way — is
that right?"* (pass the candidate through `grounds-gate.md` before it becomes a confident question).

*Why never self-resolve:* an agent filling a conflict or an unknown on its own is the origin of
spaghetti drift. The harness is accumulated, refined information, so across cycles the early
foundation's rules and this cycle's INPUT can diverge — and that conflict is more common in a delta
than in a first cycle. This generalizes the governing skill's harness-conflict rule — never resolve
an input↔harness conflict yourself — to *every* source.

## Build a presence map — but do not score it

Per axis, write down **what content landed there** — a **presence map, not a coverage measure.** Do
**not** judge whether it is sufficient or shallow: without a floor you cannot measure a gap, and the
depth floor is established in ELICIT. Estimating it here is overreach.

**Critical — "touched" ≠ "covered."** A one-line mention and a fully-specified treatment both register
as "content landed in this axis," so ELICIT must never read a non-empty axis as *done*. To stop a thin
mention from masquerading as coverage, record a **non-scoring marker of *form*** per item — e.g.
*"stated as a bare mention"* vs *"stated with rules/edges/parameters."* This is **descriptive, not a
sufficiency score** (so it doesn't violate "don't judge"), but it lets ELICIT see that a mention is
thin without DECOMPOSE adjudicating it. (This matters most for a *clean-but-shallow* design doc — every
axis looks "covered" because it's organized; the form marker is what keeps ELICIT from trusting that
surface.)

## What "don't judge" means (and doesn't) — thoroughness IS in scope

The header's "does not judge" means: do **not** resolve conflicts and do **not** score gaps. It does
**not** forbid classifying or translating — axis assignment, the premature→contract conversion, and
the keep/cut boundary are all classification judgments that belong here. **And it does NOT license a
shallow pass.** "Don't judge" is about *not resolving/scoring*, never about *extracting less*.

**Do not skim on the theory that ELICIT will re-extract — it won't.** ELICIT regenerates *dimensions a
domain kind implies* (its kind-driven lens), but it does **not** re-mine the raw INPUT — it never
sees it. A project-specific constraint you skim past here (a number buried in the brain-dump, a rule
stated once in passing) is simply **gone** from the material; that lens will not regenerate a constraint
it never saw. DECOMPOSE thoroughness is therefore **not** redundant with ELICIT thoroughness — the two
cover different failure modes, and this is the same "downstream will handle it" reward-hack that
ELICIT is forbidden (`elicitation.md`). It is forbidden here too.

## Exit bar (extraction thoroughness — judgment stays out, thoroughness does not)

Do not leave DECOMPOSE until all hold:
- **Every INPUT fragment is routed** — classified (to ≥1 axis), preserved verbatim, or
  discarded-with-a-nameable-reason. No fragment silently skipped.
- **Every non-derivable form preserved verbatim**, and every converted code block paired with its
  verbatim source where it carries a load-bearing edge (keep-biased default above).
- **Every source difference flagged** as a conflict candidate.
- **The presence map lists what landed per axis** with its form marker, and **no axis the INPUT
  actually touches is left silently empty.**

## Rules

- **Don't resolve a conflict — ask.** Don't pre-split conflict types into cases; "if it differs, ask"
  is the whole rule. (See the flag rule above.)
- **Don't guess the floor.** Produce the presence map only (what landed + its form marker); the gap calculation is ELICIT's.
- **Don't invent intent.** If it is in neither the INPUT, the code, nor the harness, do not
  manufacture it — pass it on as a question candidate.
- **Don't discard something as "wrong information."** An INPUT that differs from the code may be
  stale, or it may be the *intended change* that is the heart of this task. Don't adjudicate — flag.

## What this produces (in-session, written to no file)

(1) per-axis classified signal (2) the presence map (what landed per axis + form marker) (3) conflict/dedup
flags (4) preserved non-derivable forms. ELICIT receives these as **challengeable material** (authority demoted, utility kept — a good
INPUT's content flows almost unchanged into the spec, but only after dialogue and approval confirm
it). A thin INPUT classifies and inventories to almost nothing, with no conflicts, and passes through
small — the same mechanism, only the volume differs.

## Universality guard

Stack-agnostic. The axes (domain / technical / invariant / non-derivable form) and the
premature→contract conversion are methods that hold in any stack; what a wire format, a regen target,
or a registration point actually is, is discovered from the project at runtime — never assumed or
named as a rule here.
