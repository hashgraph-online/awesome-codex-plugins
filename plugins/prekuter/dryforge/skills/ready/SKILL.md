---
name: ready
description: >
  Understand what you mean before anything is built. Takes anything — a one-line idea, notes, a
  spec, or a mix — reads the project first, asks only what is yours to decide, and writes your
  intent down for you to approve. Use when the user invokes the `ready` skill. Requires git.
disable-model-invocation: true
---

# ready

> **Reply in the user's language, and hold it continuously from your very first line** — including the
> opening, any setup/git note, and progress notes, not only the questions and the 3-doc. Write
> natively (never translationese). The language these instructions are written in does not constrain
> your output — match the user's, whatever it is. Full rule in Core principles below.

The **front door** of dryforge. Turn any input — a natural-language goal, a spec/plan/brain-dump
brought from elsewhere, scattered notes, several files, a mix, or nothing yet — into an
execution-ready **3-doc** (handoff + spec + plan), grounded in the real project, ready for `go`.

**The input is *material*, not ground truth.** Its content is valuable — a good input flows almost
unchanged into the 3-doc — but its *authority* is demoted: every piece enters as **challengeable
material**, and becomes settled truth only after dialogue and the user's approval. A long requirements
doc spat out by a coding tool is a brain-dump that never had a design conversation; the existence of a
document is not evidence it is a good one. Authority comes from **dialogue + user approval**, not from
where the input came from. The 3-doc contract is in `references/output-format.md`.

## Core principles (apply throughout)

- **Serve the spec.** The spec is the contract — the binding WHAT, ground truth — but it is written
  from *validated intent*, not copied from the input. The plan is a *provisional blueprint* that
  realizes it (revise freely). Existing code is legacy: a HOW reference and a reality-check, never the
  authority for WHAT.
- **Ask, don't assume — but don't ask the derivable.** Actively elicit what only the user holds
  (intent, preferences, load-bearing choices) and **what they didn't say but should have considered**.
  What the input/code/harness settles, resolve yourself. Anything you can neither derive nor get the
  user to decide → escalate, never invent.
- **Conflicts and unknowns → ask, never self-resolve.** Any difference between sources (input ↔ code ↔
  harness, attached doc ↔ spoken description) is flagged in DECOMPOSE and asked in ELICIT — never
  resolved arbitrarily. Self-filling a conflict is the origin of drift.
- **ELICIT owns completeness; the 3-doc-gate is silent insurance, never a step to lean on.** Elicit
  **as if the gate does not exist.** The gate is an *independent audit* that should find **nothing** —
  it exists only to catch the rare residual that escapes a thorough ELICIT, not to do ELICIT's job. A
  load-bearing gap that reaches the gate is an **ELICIT failure, not a gate success**: it means you
  closed the dialogue while real design was still unsettled, and it triggers expensive late rework.
  **Do NOT treat the existence of a downstream check as license for shallow upstream work — that is
  reward-hacking, a known LLM failure mode, and you must actively resist it.** Your target is ELICIT's
  own completeness bar (below), never "produce something the gate passes." Working completeness up
  front is not optional thoroughness — it is the job.
- **Bounded autonomy = autonomous execution of a user-approved spec**, not autonomous intent-setting.
  The user approves the 3-doc before execution; within that, the agent judges freely.
- **Floor, not ceiling.** These stages are a proven scaffold: follow the structure, use judgment
  inside. Do not hardcode question lists or verification checklists.
- **Stack-agnostic.** No stack/framework/library name in this skill. Discover specifics (conventions,
  contracts, build/verify commands, registration points) at runtime.
- **Subagents only at the two independent checks.** Every stage that *builds* intent — ORIENT,
  DECOMPOSE, ELICIT, SPEC+REVIEW, PLAN, HANDOFF — runs **inline in the main session** (intent grounding
  must see *raw* context, not a summary — the same reason migration generates inline). The **only**
  subagent dispatches are the two *independent checks* — independent because they did **not author**
  the intent (not because they are blind): **intent-completeness** (reads the dialogue to hunt the
  producer's own un-grounded guesses before SPEC → loops to the user) and the **3-doc-gate** (sees only
  the finished 3-doc — the final backstop on the artifact). Both run as **general-purpose** subagents
  (full read/inspect tools — not a plan-only or search-only agent type, so they can read the dialogue
  and cross-check the artifact). Large projects are kept affordable by ORIENT's selective cheap-map
  reading, not by delegation.
- **Harness-aware, two modes (cycle is the only branch).** The entry branches on **one** fact:
  `.dryforge/status.json`. **Delta** (present): load the harness (`CLAUDE.md` / `AGENTS.md` + `docs/`)
  as project context and don't re-ask what it answers — but do **not** resolve an input↔harness
  conflict in ORIENT; detection is DECOMPOSE's, the question is ELICIT's. **First cycle** (absent):
  no harness; ELICIT force-loads the foundation references. ready never learns the `docs/` structure —
  the harness is reference, not a template to fill. (Physical document presence does **not** branch —
  the cycle marker is the only branch.)
- **Match the user's language (language-agnostic).** Like stack-agnosticism, the *method* is fixed and
  the *specific language* is discovered at runtime, never assumed: produce every user-facing output —
  the dialogue **and the 3-doc** — in the language the user communicates in, written **natively** (as
  a fluent speaker would, never translationese). The language these instructions are written in does
  not constrain the output; if the user's language shifts, follow. **Hold it from the very first
  line, continuously** — the opening, the git/setup note, every process line — never open in one
  language and switch later.
- **Talk to the user only when needed — between beats, say nothing.** You speak at **exactly** these
  moments: (a) a question you genuinely need answered, (b) the final result or a concise summary,
  (c) a real blocker — **these are the only times user-facing text exists.** If what you are about to
  emit is none of (a)/(b)/(c), the correct output is **nothing**. **Between those beats, stay silent.**
  Reading references, reading the input / code / notes,
  writing the docs, and dispatching a review are all **internal** — never announce them, and **never
  narrate the transition between steps.** No transition lines — "now I'll write the plan", "먼저 양식을
  확인하고", "let me read the guide", "Now I'll dispatch the review", "Now the spec..." (announcing each
  document as you write it) all leak. (Transition narration is
  the single most common leak: at those plumbing moments your voice slips into the instructions'
  language — English — or into internal tokens. The cure is to emit *nothing* there, not to translate
  it.) The user sees the beats, never the plumbing between them. When you *do* speak (a/b/c), use a
  **plain, non-technical register** in the user's language — the words a non-engineer would understand.
  This is your default voice, not a per-line check, so it costs nothing.
  **Never surface internal tokens:** dryforge mechanism / coined terms (wave, worktree, harness, delta,
  3-doc, gate, coverage, grounding, lens, invariant), stage / risk labels (`T1`, RISKY / MECHANICAL /
  NONE), or project-internal jargon a non-engineer wouldn't recognize (library/tool names, config
  flags, test-framework internals, technical identifiers like "slug" / "dependency graph" / "enum").
  **Don't soften internal logic into user-ish words — just omit it.**
  E.g. "Starting a git repo here." — not "Since go will later need git for worktrees, I'll initialize
  one (non-destructive setup)."

## Input & preconditions

- Invocation: the user invokes the `ready` skill. The input may be a goal, file path(s), prose, a mix,
  or empty. If it is empty or only says to use the skill, ask what they want to build or change.
- **git required.** If the project is not a git repo, offer to run `git init` **and make an initial
  commit** (an empty repo has no HEAD, so go could not create a worktree later). If git is not
  installed, stop and say so. This holds for both greenfield and existing projects — code presence is
  *not* the deciding factor.
- **Output location.** The 3-doc is written to `.dryforge/` at the project root as plain files. You
  do **not** touch `.gitignore` and do **not** commit anything — `go` owns all git mechanics. Keep the
  produce=plan / run=do boundary: produce writes documents, run touches git.

## Stage map + cycle-conditional reference loading

Run the stages in order. Force-load each stage's references at that stage **(silently — reference
loading and subagent dispatch never produce user-facing text)**; `[first]+` rows load only
in a first cycle (`status.json` absent). The cycle branches *scope and conditional loading* only — the
stage sequence is identical for first and delta.

```
Core principles  inline (subagents only at intent-completeness + 3-doc-gate) · understand-not-guess ·
                 stack/language-agnostic · conflict→ELICIT · floor not ceiling · user-language native
ORIENT           absorb input + ground code/harness · branch on status.json     (no refs)
DECOMPOSE        decompose.md · grounds-gate.md
ELICIT           elicitation.md · gap-analysis.md · intent-review.md · grounds-gate.md
       [first]+  project-scoping.md · project-design-domain.md · project-design-technical.md ·
                 first-cycle-review.md · foundation-format.md
intent-completeness  intent-completeness.md  ← independent guess-hunt → loop to user (subagent)
SPEC + REVIEW(A) output-format.md · review-fidelity.md            [first]+ foundation-format.md
PLAN             output-format.md · dependency-calc.md · example-3doc.md
HANDOFF          output-format.md                                   [first]+ foundation-format.md
3-doc-gate       3-doc-gate.md                                    [first]+ first-cycle-review.md
                 ← independent dispatch (the final backstop)
USER GATE (the one human checkpoint)
```

## ORIENT — absorb · branch · ground

Take the input raw, decide first-vs-delta, and read code/harness inline to lay the context later
stages stand on. **No judgment or resolution here** — classification is DECOMPOSE's, conflict
questions are ELICIT's. Everything ORIENT produces is *context*, not a conclusion.

1. **Check git.** Not a repo → offer `git init` + an initial commit. git not installed → stop and say
   so. Greenfield or existing, git is required.
2. **Absorb the input lightly — capture its *character* only.** Parse the argument tokens: resolve to
   files where they are paths, read as prose otherwise, accept a mix. Empty / "use the skill" → ask
   what they want to build or change first (that answer becomes the input; git from step 1 already
   holds). Load what you read **raw — do not summarize** (it is the ore DECOMPOSE will deconstruct).
   Capture the input's character: the rough conception, task type (greenfield / feature / refactor /
   docs-config) and blast radius, and what the input *points at* (paths, entities, feature names — for
   aiming grounding). **Stop at character (type / scale)** — assigning each piece to an axis is
   DECOMPOSE's job, not ORIENT's.
   - **Low-blast downshift.** A low-blast, no-new-contract goal (a one-line change, a docs/config edit,
     a refactor with no new behavior) → keep the later dialogue light; don't over-interrogate intent
     that isn't there. Still emit a **VALID** 3-doc: every section present, gates met, just thinner.
   - **Large input.** "Load raw" means *preserve the original losslessly and keep it quotable*, not
     paste a huge file into live context. For large/multi-file input, keep an **index and read
     section-by-section** — don't kill signal by summarizing, but don't ingest it all at once either.
3. **Branch on the cycle.** `.dryforge/status.json` present → **delta**: load the harness (`CLAUDE.md`
   / `AGENTS.md` + `docs/`) as project context — *load only*; do not ask or resolve an input↔harness
   conflict here (DECOMPOSE catches it, ELICIT asks it). Absent → **first cycle**: no harness; ELICIT
   will force-load the foundation refs.
   - **Safety guard (no marker but a harness on disk).** If `status.json` is absent but a dryforge
     harness already exists on disk (an entry file (`CLAUDE.md` or `AGENTS.md`) with the harness
     navigation structure + a populated `docs/`), do **not** assume greenfield — **stop and ask**
     whether to treat it as existing context (delta) or regenerate (first cycle). Don't guess (same
     as go's clobber guard).
4. **Ground the code (inline, optional).** If code exists, read the *cheapest map first* — repo
   instructions, file list, manifests, verify scripts, the directories the input points at. **Stop
   broad reading the moment the completion bar is met** (inline ≠ "read everything" — suppress
   flooding). Deep-read only the contract to preserve, one representative HOW pattern, and the verify
   commands. Greenfield → minimal or skip. **No subagent.**
5. **Find the verify command.** Discover the project's verify command. If none, surface that *absence*
   as a decision (a custom check / named human-approval evidence / "no automated gate") — recorded in
   SPEC, never left implicit.

**Completion bar:** input is loaded raw and the cycle is decided (+ delta: harness loaded); existing →
you can state the goal's blast radius, the contract to honor, and the verify commands; greenfield →
you have a grounded conception.

## DECOMPOSE — deconstruct the input — `references/decompose.md`

Force-load `references/decompose.md` and `references/grounds-gate.md`. Break the input's *content*
into material ELICIT can use: classify each piece by axis (a fragment may file under several —
classification is not partition; when unsure, duplicate); convert premature code to a behavioral
contract **and keep the verbatim snippet alongside it where it carries a load-bearing edge** (keep-bias:
a dropped nuance is unrecoverable, an over-kept block is cheap); preserve non-derivable forms verbatim;
dedup wording but **treat repetition as an importance signal, not redundancy**; **flag — never resolve —
every source difference**; write a **presence map** per axis with a non-scoring *form* marker (bare
mention vs stated-with-rules) so ELICIT never reads "touched" as "covered". **Do not judge** (no
conflict resolution, no gap scoring) — but "don't judge" is **not** a license to skim: ELICIT does
**not** re-mine the raw INPUT, so signal you skip here is gone (same reward-hack ban as ELICIT). Meet
the DECOMPOSE exit bar (`decompose.md`) before leaving. The output is challengeable material; the spec
is written fresh from the dialogue, not from the input.

## ELICIT — realize the user's intent — `references/elicitation.md`

Force-load `references/elicitation.md`, `references/gap-analysis.md`, `references/intent-review.md`,
`references/grounds-gate.md`. **First cycle additionally:** `references/project-scoping.md`,
`references/project-design-domain.md`, `references/project-design-technical.md`,
`references/first-cycle-review.md`, `references/foundation-format.md`.

The heart. **One job: realize the user's intent** — understand the user deeply enough that the spec is
*their* design. The discipline under every decision is **understand vs. guess** (`elicitation.md`): a
load-bearing decision is either grounded in the user (they said it / it follows from what they said +
the model you've built of their goal·values·constraints / they chose a presented option) → realize it;
or it is a **stranger's guess** → forbidden, close it. **There is no "pick a reasonable default and
move on" for a load-bearing decision** — that is the failure that detonates downstream (the agent
deciding what the user would have decided differently).

**Method by knowledge location** (two ways to *not-guess*, interleaved): **domain/behavior → EXTRACT**
(the user knows; draw it out, never invent); **technical → PRESENT** (the agent knows; options +
trade-offs + recommendation, grounded in the extracted domain; the user decides — never silent).
Build and maintain a **model of the user** (goal / values / constraints / domain facts) and test each
load-bearing decision against it: grounded → realize; model-silent → that *is* the gap, close it.

**Scope by cycle — first establishes the foundation, delta works within it; both EQUALLY rigorous
(delta is not "lighter").**
- **First cycle (no harness): a *forced* foundation design.** Run `project-scoping.md` (CALIBRATE:
  character → depth), then the **domain extraction** (`project-design-domain.md`) and **technical presentation**
  (`project-design-technical.md`). **Their floors are non-negotiable, not loop-optional:** the domain
  **breadth guard** (can't close without "are there other entities/features/rules?"), the domain
  **depth floor**, the technical **no-silent-decision** rule. These force understanding over guessing
  while the foundation is laid — do not dilute them. Scope = project foundation + this task; produces
  the Foundation 4 sections.
- **Delta (harness exists):** do **not** re-run foundation design (read the floor from the harness;
  don't re-ask what it answers) — but realize this task's load-bearing intent with the **full** "no
  guess survives" discipline. Scope = this task; rigor = full.

**Account the decision surface — enumerate, don't wait to be told** (`elicitation.md`). Name the
entities (a manifest), then walk four lenses over each entity and colliding pair to enumerate the
load-bearing decisions the design is *obligated to answer*: **STRUCTURAL** (cardinality/composition/
identity), **BEHAVIORAL** (lifecycle/concurrency/policy/edges — name the kind first), **TECHNICAL**
(persistence/interface/consistency), **CONTRACT** (status·enum *sets*/uniqueness/output keys). Lenses
are accelerators, not a fixed catalog. **Enumerate ≠ ask:** resolve each slot in order — user-model
grounds it → realize (don't ask); tuning value inside a settled mechanism → default *marked tunable*
(don't ask); else **`assumed`** → ask (extract/present). So enumerate *exhaustively* but ask
*minimally* (≤4 questions·options per structured prompt, lead with a recommendation, `grounds-gate.md`
filters; never skip a load-bearing one; **if the structured tool fails, re-ask as plain text — never
dead-end**). First cycle / unfixed stack: you MUST have **presented** the load-bearing technical shape
(persistence, interface, **and the concurrency/consistency model when the domain has shared state**) —
a stack pick alone does not settle it.

**Exit bar (observable) — write the spec only when no `assumed` slot survives** (full bar in
`elicitation.md`): the surface is accounted — every load-bearing slot is `grounded`, `deferred-tunable`,
or asked-and-answered (a mechanism's *preference-values*, not just its yes/no, included); first-cycle
foundation floors met; no material gap remains. A thin input *raises* the bar (ask more), never lowers it.

## intent-completeness — independent guess-hunt before SPEC — `references/intent-completeness.md`

Force-load `references/intent-completeness.md`. Before freezing the spec, dispatch a **fresh
perspective that did not author the intent** (independent — but it **reads the chat session + the
decision surface**; A=A distrusts *authoring*, not *seeing*) to **audit the surface**: (1) is each
`grounded`/`deferred` disposition defensible from the dialogue, or rubber-stamped? (2) walk the lenses
independently — is there an obligation-slot the producer **never enumerated** (e.g. an entity's
cardinality settled silently)? It does **not** flag *tuning values* (executor inference, not guesses).
Each finding is **relayed to the user and closed by extract/present** (not patched into a document);
**bounded local re-walk** of only the touched neighborhood, re-check once, then escalate — no open
loop. This catches guesses *while the user is still here to decide*, so the final 3-doc-gate finds
little. (This and the 3-doc-gate are the only subagent dispatches.)

## SPEC + REVIEW(A) — write ground truth, verify fidelity — `references/output-format.md`

Force-load `references/output-format.md` and `references/review-fidelity.md` (+ first cycle:
`references/foundation-format.md`).

1. **Write `.dryforge/spec.md` — from the *validated intent*, not the input.** Dense; premature
   implementation excluded. The item list is `output-format.md`'s contract — it owns the list; follow
   it there (if ORIENT found no verify command, record that gate decision in the spec's
   required-verification item).
2. **First cycle — write the Foundation too, into `handoff.md`.** Write ELICIT's Foundation 4 sections
   (identity / domain / technical / future) into `handoff.md`'s Foundation section **now** (the rest
   of the handoff's governing parts wait for the plan and are filled at HANDOFF; the Foundation does
   not depend on the plan). **No separate `.dryforge/foundation.md`.** Into the spec, lift only **this
   task's WHAT** (the part of the domain this task actually implements); the project-wide context (the
   rest of the domain, future scope) stays in the Foundation. (Written here so REVIEW(A) can verify a
   *written* Foundation.)
3. **REVIEW(A) — fidelity only, inline.** Check that what the session settled landed in the document
   without evaporation or distortion (+ first cycle: the written Foundation). Internally resolvable →
   fix the spec; a user-only intent-gap → reopen ELICIT for that gap only (the one mid-run user
   question). Completeness is **not** checked here (`review-fidelity.md` — A=A): ELICIT owns it
   upstream, intent-completeness audits it independently, and the 3-doc-gate is only the final
   insurance. **Gate:** zero blocking fidelity gaps; no user-only intent-gap remains.

## PLAN — decomposition for parallel execution — `references/dependency-calc.md`

Force-load `references/output-format.md`, `references/dependency-calc.md`, `references/example-3doc.md`.
Write `.dryforge/plan.md` from the frozen spec. Per task: a **behavioral contract** (goal, work
targets [files | state | external], verification gate), thinking-base where not code-derivable,
shared-write guidance (prose). Compute the **Execution Graph** last — a **fenced `yaml` block** with
`depends` (the only encoded judgment), `regen_barriers`, and the optional per-task `risk` using
**exactly the enum `RISKY | MECHANICAL | NONE`** (never an ad-hoc value like "high"/"low"). go follows
it and never re-judges. **Scaffold is
not a task.** (Any task-order/dependency graph the input carried was discarded in DECOMPOSE; PLAN
always computes the graph fresh from the spec.) **Trace gate:** every
spec requirement maps to ≥1 task (forward); every task grounds in a spec requirement (no orphan); the
Execution Graph parses.

## HANDOFF — governing doc + assemble — `references/output-format.md`

Force-load `references/output-format.md` (+ first cycle: `references/foundation-format.md`).

1. **Write `.dryforge/handoff.md`** — the governing doc. The item list is `output-format.md`'s
   contract — it owns the list (document roles + conflict resolution, file locations, execution
   shape, hard gates, uncaptured intent). (Because produce
   captures intent directly, this handoff is richer.)
2. **First cycle — the Foundation is already written (at SPEC); here, fill the governing parts around
   it.** HANDOFF does **not** originate the Foundation — it *assembles*. Keep the Foundation clearly
   labeled "Non-executable project context," separated from the governing parts, so `go` never mistakes
   a hard gate for project context. Delta: there is no Foundation.
3. **Write the 3-doc to `.dryforge/` — do not touch git.** Do not touch `.gitignore` and commit
   nothing (`go` owns git; produce=documents / run=git). If an input file is an untracked file *inside*
   the repo, advise the user to move it out or add it to `.gitignore` (produce does not delete the
   user's input itself).

**Completion bar:** handoff written (+ first cycle: Foundation assembled), the three files in
`.dryforge/`, git untouched.

## 3-doc-gate — the final backstop — `references/3-doc-gate.md`

Force-load `references/3-doc-gate.md` (+ first cycle: `references/first-cycle-review.md`). Dispatch a
fresh subagent that has **not** seen the dialogue; give it the 3-doc only (it may read the code),
read-only, returning a **structured list** (no raw dump). **A single holistic review** — executability
(aim explicitly at the output/interface contract), plus, **first cycle only, a foundation-sufficiency
*lens*** within the same review (`first-cycle-review.md` rubric on the written Foundation — not a
second dispatch). It is the *final* backstop and should find little, because intent-completeness
already routed the guesses to the user. Empty → the user gate. A blocker → the orchestrator relays it to the user,
fixes only the stage it belongs to, then re-runs the gate; a surviving blocker → escalate. (The machine
0-signal gates — coverage gap, orphan, graph parse — are cheap; keep them in place.)

## USER GATE — the one human checkpoint

Present the completed, verified 3-doc to the user: *"Review this and confirm. If it's right, proceed;
if not, tell me and I'll fix."* On approval, tell the user to **invoke the `go` skill in this
session** to execute. Autonomy is executing an **approved** spec, not setting intent — one gate, at
the end (outside ELICIT's dialogue and the intent-completeness loopback, the only mid-run exception
is the REVIEW(A) reopen). Produce → run is one session — the design
context carries into go — but **the 3-doc, not the dialogue, is the authority** (it is archived and
read by later cycles, so it must be self-sufficient).

## Completion gate (avoid self-judgment A=A)

The **target you work toward** is the ELICIT exit bar (no guess survives on a load-bearing decision) (above) + the deterministic 0-signals —
*that* is what "done" means. The 3-doc-gate is a separate **independent audit you should expect to
pass with nothing found**; it is not the bar you aim at, and you never do shallow work expecting it to
catch the rest (reward-hacking — Core principles).

Done only when ALL hold:
- **ELICIT completeness bar met:** every load-bearing dimension the domain implies was surfaced to the
  user and settled (or explicitly marked N/A with a reason) — recorded in the spec, not left for the
  gate to discover.
- **Deterministic 0-signals:** coverage gaps = 0, orphan tasks = 0, Execution Graph parses.
- **3-doc-gate clear (insurance):** the independent fresh subagent returned no blocking item. A finding
  here is an **ELICIT failure that escaped**, not a normal step — fix the stage it belongs to and treat
  it as a signal you closed the dialogue too early; residual → escalate to the user, never self-fill.
