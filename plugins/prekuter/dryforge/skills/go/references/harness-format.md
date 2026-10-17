# harness-format.md — the project harness spec (force-load)

The operational spec for a **project harness**: the durable documentation layer dryforge writes
for a project (created by `migration`, created/updated by `go`). This file is the **runtime
authority** — what each file is, what it must contain, the bar its content must clear, and how it
is created and updated. It carries the rules, not the design rationale.

The harness is the project-lifetime layer, distinct from the per-task 3-doc. It occupies the
platform harness paths (`CLAUDE.md` / `AGENTS.md`), so every agent working the project — dryforge
or not — operates inside it. It is a **durable project constraint** (the project's discipline and
memory), not ground truth: an active task's spec works *within* the harness, never overrides it
silently — a conflict is escalated to the user (see "Conflict" below).

**The harness is the sole durable store for project knowledge.** Anything you learn about *this
project* that is worth keeping — a trap, a non-obvious mechanism, a decision and its reason, a run
procedure — goes into the harness (engineering-notes / operations / decisions / the matching doc),
**never into the agent's own host memory or any external / per-agent memory store**. Host memory is
private to one agent on one platform and invisible to the next agent and to other agents' entry
points; project knowledge parked there is lost to everyone else and to the next cycle. The
harness is portable, shared, and committed with the project — it is the one place durable project
knowledge belongs.

## Language

**Language-agnostic.** Write the **entire harness in the language the user communicates in**, natively
(as a fluent speaker of that language would, never translationese). The *method* is fixed; the
*specific language* is discovered at runtime, never assumed — exactly as stack specifics are. The
language this spec is written in does not constrain the harness.

## Structure

Every file has a fixed slot. A missing file that the project needs is a defect. An *empty* file is
correct only when its category genuinely does not apply to this project; an empty file for a
category that *does* apply is a hollow shell — a defect.

```
project-root/
├── CLAUDE.md                     ← Claude Code entry point
├── AGENTS.md                     ← agent entry point (identical content to CLAUDE.md)
├── docs/
│   ├── architecture.md           ← system composition
│   ├── business-rules.md         ← domain logic
│   ├── security.md               ← security policy
│   ├── standards.md              ← rules (hard gates, conventions)
│   ├── engineering-notes.md      ← knowledge (traps, mechanisms, checklists)
│   ├── operations.md             ← operations (setup, build, deploy)
│   ├── contracts.md              ← external interface contracts
│   └── tracking/
│       ├── status.md             ← current position vs full scope
│       ├── decisions/
│       │   ├── index.md          ← ADR index
│       │   └── NNNN-<slug>.md     ← individual decisions
│       └── findings.md           ← unresolved problems
└── <module>/
    └── AGENTS.md                 ← per-module scope, boundaries, invariants
```

`.dryforge/` (the 3-doc, `NNN/` archives, `backup/`, the local `status.json` marker) is the
per-task workspace, **not** part of the harness — the harness never references it (see
self-containment).

## Content quality — the bar every file must clear

A harness whose structure is filled but whose content is hollow is **worse than none**: the next
agent sees "docs exist," assumes it is informed, and works uninformed. The single purpose of every
file is that the next agent reads it and can work the project without going off the rails. Do not
satisfy this with structural box-filling — drive content density in prose.

**Five principles — does this sentence earn its place?** (apply to every file)

1. **Non-derivability** — if reading the code reveals it, don't write it. The harness exists for
   what code cannot express: intent, constraints, the reason behind a decision, domain knowledge,
   non-obvious mechanisms.
2. **Work-changing** — an agent that reads the sentence and one that doesn't must produce different
   work. If the work is identical, the sentence is decoration, not information.
3. **Density** — every sentence carries a core fact. Information density, not word count, sets a
   document's value.
4. **Project-specificity** — a fact true of any project is not worth writing. Only this project's
   decisions, constraints, and mechanisms.
5. **Consequence-of-absence** — "if this sentence were missing, what breaks?" No answer → cut it.
   An answer → that consequence is the sentence's weight.

**Four techniques — how to state what survived the principles:**

1. **Verifiable statements** — every rule/constraint written so "was this honored?" is decidable.
2. **State the counter-case** — pair each "must" with its "must not."
3. **Describe the mechanism** — not just the outcome: input → processing → output.
4. **Make edge cases concrete** — never "handle other cases appropriately"; give each edge a
   specific disposition.

**The harness describes the *project* only — not itself, its origin, or the tooling.** Never write:
- **The document talking about itself** — its state, thinness, completeness, lifecycle, maturity, or
  *why it exists / how to read it* (e.g. "read this instead of the code", "written so you can derive
  tests without reading the source"). State the project fact directly; don't narrate the doc's role.
- **Its origin or creation** — that it was generated, migrated, or a first-cycle artifact; and never
  list the documentation layer itself as a deliverable (status.md must not record "created the docs/
  layer" as done — docs are not a shipped project capability).
- **The generating tool or dryforge's coined vocabulary** — "dryforge" never appears in a generated
  project, nor do its internal coinages used to label the doc system ("harness", "3-doc", "delta",
  "migration"/"wave" as process names). Name sections in the project's own plain terms ("Project
  structure", not "Harness navigation").

(Current *project* state — "cycle 1 built the catalog" in status.md — is fine; commentary about a
*document's* own maturity, purpose, or origin is not.)

## Entry point — CLAUDE.md / AGENTS.md

Two files, **identical content**, different platform. Write both together, byte-for-byte the same.

Must contain:
- **Project overview** — what this project is, its scale, and who it is for, in 2–3 lines. Lets an
  agent register the project's scope before working. This is where drift-prevention pays off most:
  an agent that doesn't know the project's scale and character will introduce technology that
  doesn't fit it, or over-engineer a single feature.
- **Navigation tree** — show the **whole harness** as a single project-root directory tree:
  `CLAUDE.md` / `AGENTS.md`, the `docs/` subtree, **and the module `AGENTS.md` at their actual
  directories** — each path annotated with an arrow + a one-line role. A **tree** (`├──` / `└──`),
  **never** a table, a flat list, or just the `docs/` subtree with modules tacked on flat below — one
  coherent tree so structure + purpose register at a glance.
- **Hard gates** — a **curated highlight** of the project's top non-negotiables (3–5, for at-a-glance
  before reading docs/). This is a highlight, **not** the full normative set: `standards.md` holds
  the authoritative complete rules (the navigation tree points there). Don't restate the full
  standards / verify-gate list here — surface only the headline non-negotiables.
  **Hard gates are permanent project invariants, not this-cycle scope boundaries.** "Don't build
  feature X yet" is **not** a hard gate — unbuilt-but-planned scope lives in `status.md`'s "remaining"
  (it's a *status*, not an invariant; a later cycle will build it, and a permanent don't-build gate
  would falsely conflict with that cycle — a cycle's scope-freeze belongs in its 3-doc, not the
  harness). **Forward-compat is not a hard gate either.** "Keep it compatible with planned scope" is
  not a permanent invariant: a genuinely structural rule (e.g. "storage stays behind the Store
  interface") is just a dependency/boundary rule → `standards.md`; anything that *preserves a current
  shape so future work can attach* is maintain-guidance → `status.md`'s remaining or
  `engineering-notes.md`. Never write a "keep shape Y" gate — especially when a remaining-scope item
  will change shape Y (that is a scope-freeze wearing a forward-compat label).
- **Pre-work checklist** — the baseline reads (`docs/standards.md`, `docs/engineering-notes.md`, the
  relevant module's `AGENTS.md`) **plus project-specific targeted reads**: before a given kind of
  risky work, which section/pattern to read first (e.g. before touching authorization, the security
  model + the auth-helper pattern; before a schema change, the migration trap in engineering-notes).
  A generic "read these three files" alone is low-value — make it project-specific.
- **Problem-routing** — name the project's **specific critical-failure conditions** (what is critical
  for *this* project — e.g. data-isolation breach, authz bypass, migration corruption) → report to
  the user immediately; everything else → record in `docs/tracking/findings.md`. Not generic
  boilerplate.

Handling an existing entry file (CLAUDE.md / AGENTS.md): (1) back up each one that exists to
`.dryforge/backup/`; (2) review the old content **critically** — do not transcribe it. Decide which
dryforge document each piece belongs in, drop what the new `docs/` already covers, and
improve/re-state what is worth keeping; (3) present the review to the user (what went where, what
was dropped and why) and get approval; (4) rewrite into the dryforge structure (approved content
only).

## docs/ file specs

Each file is **self-contained** and written at **one altitude**. "What to include" defines a *kind*
of information, not a stack or domain — if the project has none of that kind, the item may be empty.

### architecture.md — system composition
- **Purpose**: the project's technical whole — what the components are and how they connect.
- **Altitude**: system level (relationships and data flow between components).
- **Include**: component topology (what talks to what, and how); the end-to-end flow of a
  representative request/operation; the module/component map (name · role · dependency direction);
  external-system dependencies. Name the stack's components **where they sit in the topology/map**,
  not as a standalone front "tech stack + why we chose it" section.
- **Exclude**: domain rules; security-policy detail; code conventions; traps/workarounds; **a
  standalone tech-stack listing or generic stack-choice rationale** — the one-line stack identity is
  the entry-point overview's, and a stack-choice rationale belongs in `tracking/decisions/` only if it
  carried a real trade-off (a generic "standard setup works here" rationale is filler — cut it).
- **Quality floor**: every component has a stated role and dependency direction; at least one
  representative flow is traced from entry point to final response; where the system has a boundary,
  state what crosses it and what does not. Not "uses a modern architecture" (a modifier with no
  structural fact) — the concrete A → B → C connection and its protocol.

### business-rules.md — domain logic
- **Purpose**: the canonical source for the business rules the code must implement — the definition
  of behavior itself, not how it is implemented.
- **Altitude**: domain level (behavior, invariants, edge cases).
- **Include**: relationships and invariants among domain entities; state transitions (both the
  possible and the impossible ones); calculation logic (input → processing → output as a clear
  formula); explicit disposition of edge cases; domain-term definitions (where the same word means
  different things in different contexts, distinguish them).
- **Exclude**: implementation (which class/function handles it); auth mechanisms (→ security); code
  patterns (→ standards).
- **Planned scope is not a permanent rule.** A capability that is unbuilt but planned (in
  `status.md`'s "remaining") must not be written here as a permanent domain impossibility — describe
  the *current* state ("currently one currency per group"), never a permanent ban ("mixing currencies
  is impossible by construction") for something a later cycle will build.
- **Quality floor**: every rule is verifiable — a test case is derivable from the rule alone; every
  "must" has its paired "must not"; mechanism, not just outcome ("when A and B hold simultaneously,
  transition to state X," not "becomes state X"); no "handled appropriately" on an edge — each edge
  gets a concrete disposition.

### security.md — security policy
- **Purpose**: what is protected, who may do what, and what is recorded.
- **Altitude**: policy level (protected assets, access rules, audit scope).
- **Include**: the authentication flow (the steps from entry to authenticated, including each step's
  failure path); the authorization model (a complete subject · action · condition matrix); audit
  targets (the concrete list of events that must be recorded); credential management (lifetime ·
  revocation · storage · rotation); sensitive-data policy (what is sensitive and how it is handled).
- **Exclude**: domain rules; system topology.
- **Quality floor**: the auth flow names failure paths (bad credential, expiry, lockout, ...), not
  just the success path; authorization states what is *explicitly not allowed*, not only what is;
  audit targets enumerate concrete events, not "sensitive operations"; credentials are covered from
  creation to destruction. Not "follows security best practices" — this project's own security
  decisions and their consequences.

### standards.md — rules
- **Purpose**: what breaks when violated. The project's hard gates.
- **Altitude**: normative level (MUST / MUST NOT).
- **Include**: dependency-management approach; commit/branch rules; verification gates (the
  conditions to pass before merge/deploy); module-boundary rules (what may import what);
  naming/structure conventions; input/output contract patterns; environment-config rules.
- **Exclude**: traps or debugging knowledge (→ engineering-notes); domain rules (→ business-rules);
  **the external API's status-code / error-format mapping** (→ contracts.md, the single source) —
  standards covers internal I/O contract *patterns/rules* (registration, naming), not the consumer
  wire contract.
- **Code-enforced domain invariants: state only the structural/enforcement angle here.** When a
  domain invariant is also enforced in code, standards records the **structural rule** ("no direct
  price field on the entity", "every variant write goes through service validation") and the
  **verification** ("tests must cover this invariant") — **not the invariant's content**, which stays
  in business-rules. Don't restate the invariant itself in standards (that's a business-rules altitude
  leak).
- **Not a standards rule: the current cycle's scope-freeze.** "Don't build feature X yet" is a
  *status* (→ status.md's "remaining"), not a permanent MUST/MUST-NOT. standards holds only
  permanent rules.
- **Bar**: only what leads to a build failure / test failure / runtime error / structural mismatch
  when violated. Preferences ("it'd be nice if...") are not rules.
- **Quality floor**: every rule has a clear violation criterion — a rule whose violation can't be
  judged is not a rule; record only rules actually in force (not planned or recommended); add a
  reason only when the rule is surprising (counter-intuitive). Not "follows clean-code principles" —
  "module A may not reference module B directly — they communicate only through the shared contract."

### engineering-notes.md — knowledge
- **Purpose**: what traps you if you don't know it. Practical knowledge distilled from experience.
- **Altitude**: practitioner level (symptom → cause → response).
- **Include**: traps found by debugging (observed symptom, root cause, fix/workaround);
  explanations of non-obvious mechanisms code can't reveal; distilled checklists for repeated work
  (including verification steps); counter-intuitive behavior of frameworks/tools.
- **Exclude**: rules (→ standards); domain rules (→ business-rules).
- **Trait** (author guidance — do **not** write this into the doc): may be thin in the first cycle;
  it thickens each cycle. The file contains only knowledge items — never a note about its own
  thinness or lifecycle.
- **Quality floor**: each item is symptom (what is observed) → cause (why) → response (how to
  fix/avoid); checklists don't end at "do X" but include "verify with Y"; never state what is
  obvious from the code — only knowledge unreachable from code alone. Not "edit the config file" —
  "editing config file A requires editing B too — the build system reads them independently, so a
  mismatch is silently ignored at runtime."

### operations.md — operations
- **Purpose**: everything needed to run the project, from setup to deploy.
- **Altitude**: procedure level (run it in order and it works).
- **Include**: initial setup order (with prerequisites, as runnable commands); dev/build/verify
  commands; the environment-config list and what each means; data-initialization procedure (if
  any); deploy procedure (if any).
- **Exclude**: code rules (→ standards); system composition (→ architecture).
- **Quality floor**: the setup sequence starts from prerequisites and is copy-paste runnable; each
  command's ordering dependency is clear (state where reordering would fail); environment config is
  described by role and valid scope, not just name. Not "set up the environment" — a runnable
  command sequence with each step's prerequisite.

### contracts.md — external interface contracts
- **Purpose**: the contract this system's *consumers* must hold to. Promises from the consumer's
  point of view.
- **Altitude**: interface level (the externally exposed promise, not internal implementation).
- **Include**: how consumers authenticate/access; the interface catalog (how to call · input format
  · output format · error cases); common conventions (state a recurring pattern once);
  async/event interfaces (if any). This is the **single source** for the consumer wire contract
  (status codes, error-body shape) — other docs don't restate that mapping.
- **Exclude**: internal implementation; domain rules.
- **Trait**: may be empty if there is no external interface. The interface form varies by project
  type (API, CLI, library public surface, plugin interface, event protocol, ...).
- **Quality floor**: every interface point states all three of input · output · error; common
  conventions are stated once, not repeated per interface; a consumer can integrate correctly from
  this file alone — a contract you must read the code to learn is undocumented.

### tracking/status.md — the dashboard
- **Purpose**: the current position against the project's full scope. The other `docs/` describe the
  target state (full scope); status.md shows "where are we now" against it.
- **Include**: what is done (per feature/module); what remains (the still-unimplemented parts of the
  full scope, in priority/dependency order); blockers (if any).
- **Update**: every cycle.
- **Quality floor**: a "done" claim must reflect the *actual verified state*, and **distinguish built
  from verified**. Don't mark code "test-passing" unless its tests actually exist and pass — code that
  is implemented but has no tests is "built, untested" (state it that way; the coverage gap is itself
  signal, not something to bury under a blanket "done"). Ground the claim in real evidence (the
  project's verify commands, or the observed test state); never infer a pass from "it's built" or "it
  looks done." "Remaining" is a concrete item from the `docs/`-described full scope — no vague "needs
  improvement." This file alone makes the project's progress immediately legible.

### tracking/decisions/ — decision records (ADR)
- **Structure**: a folder. `index.md` (the index) + individual `NNNN-<slug>.md`.
- **Criterion**: only decisions with a real trade-off. Don't record a choice with no alternative or
  an obvious one. Test: "could another team in the same situation have chosen differently?" — if so,
  it's a record.
- **Each decision**: context (why the decision was needed); decision (what was chosen); alternatives
  (what was not chosen, and concretely why); consequences (the constraints/effects this imposes on
  future work, including what it made impossible).
- **Quality floor**: context states the concrete situation that forced the decision; alternatives
  give specific rejection reasons, not "considered but rejected"; consequences include what is now
  impossible.

### tracking/findings.md — unresolved problems
- **Criterion**: only problems not resolved on the spot. A problem fixed in place is not recorded.
  Structural problems, problems needing code changes, known constraints.
- **Duty before listing**: try to solve it first. If the cause is traceable and fixable, fix it —
  and record the knowledge gained in engineering-notes; if a new rule is needed, add it to
  standards. **findings is the place for "cannot be solved in the current session," not "too tedious
  to investigate."** On listing, always state *why it can't be solved now* (external dependency,
  out of scope, needs a higher-level decision, ...).
- **Each problem**: what is broken (reproducibly); why it matters (blast radius); why it can't be
  solved now; a possible approach (if any).
- **Quality floor**: each problem is "under condition C, symptom S is observed," not "X is wrong";
  state the blast radius (what breaks if left). An item with no "why not now" is not a finding — it
  is unfinished work; solve it or move it to engineering-notes/standards.

## Module AGENTS.md

One per meaningful unit (module, service, package, app, ...).

- **Include**: scope (what this module owns); boundaries (what it does *not* own, what not to
  touch); invariants (what must always hold); core implementation patterns (this module's own way);
  test guidance (what must be tested, what edge cases exist).
- **Altitude**: implementation level (maps directly to code).
- **Location**: the module's root directory.
- **Module identification** — discovered at runtime. Read the project structure and identify
  cohesive functional units. Forms differ per stack, so don't hardcode; minimum heuristic: a unit
  that *has an independent entry point/interface, or is an independent build/test unit, or has an
  explicit boundary (directory + manifest)*. One or more → a module candidate. **Exclude** generated
  code, vendored or installed dependency directories, and example/test-only directories.
- **Quality floor**: scope states "Y is not this module's scope," not only "this module does X";
  invariants are verifiable statements; boundaries are concrete — not "doesn't touch other modules"
  but an explicit list of which modules/areas are off-limits.

## Self-containment rules

1. **No cross-references between `docs/` files.** Not "see the other doc" — state what is needed, at
   this file's altitude, inside this file.
2. **The same topic may appear in several files — but each describes it only at its own altitude.**
   Altitude assignment test: "who consumes this information?" Whole-system reader → architecture;
   feature-rule reader → business-rules; module-code editor → AGENTS.md. Don't replicate an upper
   altitude's detail at a lower one, or mention a lower altitude's implementation at an upper one.
3. **The harness never references the 3-doc.** The 3-doc is archived after a task completes, so a
   pointer to it would dangle.
4. **A module AGENTS.md references no other module AGENTS.md and no `docs/` file.**
5. **No constraint-ID label scheme; restate, don't reference.** The harness carries **no**
   cross-referenceable constraint IDs — not the 3-doc's `INV-N` / task `T-N`, nor any `XXX-N` scheme of
   its own. Invariants and rules are stated **by content** (the content-name is the stable handle —
   e.g. "the data-isolation invariant"), and **every doc restates the slice of a constraint it needs
   at its own altitude** instead of pointing — to another `docs/` file or to the archived 3-doc — by
   label. Restating is required even though a label reference (`(INV-1)`) is shorter: the harness must
   be self-contained and the 3-doc is ephemeral (archived after the task), so any such label becomes a
   dangling pointer. (The 3-doc itself may use `INV-N` while active — this rule is harness-scoped.)

## Conflict (task vs harness)

When a task must contradict an existing harness decision (e.g. a changed auth approach): detect the
conflict, sort out which part is a trade-off and which is a defect, and report to the user. The user
decides; the decision flows into the spec, and `go`'s delta updates the harness. The spec does not
override the harness — **the user's decision changes both at once.** Domain conflicts don't
self-resolve; the user always decides.

## Update rules

### First creation (the first `go` cycle's wrap-up, or `migration`)
- Generate the whole `docs/` structure (all files).
- Generate CLAUDE.md / AGENTS.md.
- Generate module AGENTS.md (per identified module).
- If a CLAUDE.md or AGENTS.md exists, back it up and rewrite (see entry-point handling).

### Delta update (`go`, second cycle onward)
- **Read the current `docs/` first and treat it as the existing project constraint** — no separate
  tracking mechanism.
- Update only the area matching this cycle's task scope + code diff (scope-limited delta).
- Don't touch existing content outside the change scope — whether hand-edited or written by a prior
  dryforge run.
- Where this cycle must change something that already has different content in scope: **escalate to
  the user.**
- New module added → create its AGENTS.md (and update the entry point's navigation tree).
- status.md: every cycle. engineering-notes.md: add non-obvious facts found while implementing.
  decisions/: add this cycle's trade-off decisions (only if they meet the criterion). findings.md:
  update on find/resolve.

### Which file to touch (delta)
Identify the relevant files from the 3-doc's task scope + the actual code diff:
- architecture.md — only on structural change (new service, new dependency, flow change).
- business-rules.md — only when a domain rule is added/changed.
- security.md — only on a security-related change.
- standards.md — only when a new rule/pattern is introduced.
- contracts.md — only when an external interface changes.
- operations.md — only when infra/environment/run-method changes.

**Delta is bidirectional.** A delta update is not only "add new content." Verify that this cycle's
change has not invalidated an existing statement elsewhere. Updating stale content matters as much
as adding new content.

## Execution discipline (when authoring the harness)

- **Explore sources before writing.** Explore every available source (code, 3-doc, the user
  conversation, existing docs) enough to fully understand the project *before* writing. Don't start
  writing from partial understanding.
- **Don't write off what you don't know.** Where uncertain, read more code, trace the mechanism, and
  generalize to a substantive project-specific fact. No guessing, no generalities. What the code
  can't settle, ask the user.
- **Verify against the source.** After writing, cross-check both ways: what the code has but the doc
  lacks (omission), and what the doc has but the code lacks (hallucination — except content that
  derives from future scope, which is correct, see harness-review.md).
- **A discovered contradiction is not propagated.** When sources conflict — an existing doc vs the
  code, two existing docs, or a claim you can't confirm (e.g. a README claiming one minimum runtime
  version while the manifest pins another) — do not copy both sides into the harness. Reconcile from
  the authoritative source (code / manifest / config is ground truth for *what currently is*; for
  *what should be*, the user decides) and write the single reconciled fact. If it can't be resolved
  from a source, record it in `findings.md` (with the conflict and why) or escalate — never leave
  two statements that can't both be true.
- **Filling files is not the goal.** The goal is the next agent working this project without going
  off the rails. A sentence that doesn't serve that goal is not written, however accurate.

## Universality guard

Stack-agnostic throughout. Every concrete artifact kind named above is an *illustration* of a kind
of information, never a required stack/architecture — the actual shapes are discovered in the
project at runtime. If you cannot generalize something, ask the user; never hardcode a stack.
