---
name: brainstorming
description: "Use when defining ambiguous or high-complexity new features, product behavior, UI/component design, architecture choices, contract changes, or when grilling/pressure-testing a plan or design. Routine small requests stay on the fast path."
---

<EXPLICIT-MODE-GATE>
If activation mode is explicit (`~/.config/aegis/config.toml` has
`activation_mode = "explicit"`, or `AEGIS_ACTIVATION_MODE=explicit` is visible
in the environment) and the current user request did not explicitly invoke
Aegis or this skill by name, exit back to the fast path: answer concisely
without this workflow's checklist, ceremony, or document requirements. If the
user explicitly named Aegis or this skill, proceed normally.
</EXPLICIT-MODE-GATE>

# Execute

→ Direct grilling or plan/design pressure-test? → Enter `Grilling Mode` below. Soft challenge intent? → Use its one-line mode confirmation. Do not start normal design artifacts, document writing, task planning, or implementation during the interview.
→ New feature, product behavior, UI/component design, architecture/contract change, or ambiguous medium/high-complexity work? → **Design first. No implementation until the needed design/spec is approved.**
  1. Explore project context → read authority docs, check for existing patterns
  2. Ask clarifying questions one at a time (prefer multiple choice)
  3. Propose 2-3 approaches with trade-offs and your recommendation
  4. Present design sections → get user approval after each
  5. Write spec → self-review → user review → transition to writing-plans
→ HARD GATE: For tasks that match this skill, do NOT write code, scaffold projects, or invoke implementation skills until design/spec approval is satisfied.

## Route Fixtures

These rows are calibration expectations for method behavior, not a runtime
regex router. The Agent selects the route from evidence; route selection is
not a user question.

| Scenario | Route |
| --- | --- |
| 想法还没想清楚，先梳理功能设计 | normal brainstorming, compact output first |
| 讨论公共 API 契约和兼容边界 | normal brainstorming, design sections before implementation |
| 盘问/拷问/审问这个方案，不要顺着我 | `Grilling Mode` |
| 修复登录按钮的空指针 | `systematic-debugging` |
| review 当前 PR / diff / 当前代码 | `requesting-code-review` |
| 给我一个有目标的方案 | `goal-framing` when goal intent is explicit; otherwise normal brainstorming |
| 把按钮文案从保存改成提交 | fast-path; no design ceremony |

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context and authority boundary, then ask questions one at a time to refine the idea. Once you understand what you're building, present the smallest design artifact that stabilizes the work and get the required approval.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take implementation action for work that matches this skill until you have presented the required design/spec and the user has approved it where this workflow requires approval.
</HARD-GATE>

## Grilling Mode

### Mode Precedence

While Grilling Mode is active, it overrides the normal brainstorming execution
flow. Suspend `Checklist`, `The Process`, the `Compact output contract`, and
all documentation or design-transition requirements until the user exits the
interview; retain the no-implementation hard gates.

### Grilling Entry Signals

- **Direct:** The user asks to grill or interrogate an idea, plan, or design, or explicitly requests a pressure-test. Direct phrases include `grill me`, `grill this plan`, `审问我`, `盘问我`, and `拷问我`. Enter the mode immediately.
- **Soft:** The user asks to challenge assumptions, find holes, red-team, or "别顺着我" about a draft idea, plan, or design. Ask only: `Grill or normal brainstorming?` Enter the mode only after confirmation.
- **Not grilling:** A bare/literal phrase reference, or a PR, diff, or current-code review. Explain literal phrases normally; route implementation review to `requesting-code-review`.

### Opening Card

After the user has entered the mode, emit this once in the user's language, then begin the interview:

```text
◆ Grilling Session
Target: <idea / plan / design>
Question path: value -> boundaries -> failure modes -> acceptance
Pace: deep (default) | fast (user-requested)
```

### Pace

- **Deep:** Ask exactly one decision question per turn when it is blocking or depends on the previous answer. State the recommended answer and the most relevant trade-off before waiting.
- **Fast:** Only when the user explicitly asks for a fast or batched interview (for example, `fast`, `batch`, `快问`, or `一次问几个`), ask at most three independent decision questions. Give each question its recommendation and trade-off, then wait for the user's responses. Return to deep pace for dependent follow-ups.

1. Explore the codebase and current authority docs for facts before asking. Do not ask the user for facts that can be found locally.
2. The user owns the decision. Do not treat a recommendation, a tentative answer, or a shared-understanding checkpoint as final approval.
3. Aside from the one-time opening card, keep the turn to the observation, recommendation, and the selected pace's questions. Do not emit a full design ceremony, write docs, create a plan, or implement while the interview is active.
4. End when the user says to stop, defer, or that the questions are sufficient. Reconfirm in a structured `Challenge Result`. That summary does not grant completion authority.

```text
Challenge Result
- Survived assumptions
- Rejected assumptions
- New evidence needed
- Design changes required
- Residual risks
- Return state: interview | design | approaches | writing-plans
```
5. If the user asks to proceed after the interview, return to the normal brainstorming design gate. A design/spec still needs the required approval before planning or implementation.

## Route Away / Doc Necessity Gate

Do not force this workflow onto low-complexity work. A tiny
wording edit, single-owner bug fix, simple config/status question, local
utility change, or mechanical multi-file change can proceed through concise
intent, baseline check, TDD/debugging, and verification without any new
document. Run the Doc Necessity Gate before writing any spec, plan, ADR, or
baseline artifact:

1. Does an existing spec/plan/ADR/baseline already cover this change surface?
   -> Update that owner document in place; never create a sibling document.
2. Is the surface durable/irreversible (schema, public API, owner, dependency
   direction, migration, compat-path retirement), cross-session/cross-person
   handoff, approval-gated, or authority-required?
   -> Yes: write the smallest artifact for that surface (see Documentation).
   -> No: write no document; keep compact drafts in-session.
3. Re-check at edit time and at closeout; escalate to the smallest stabilizing
   spec if uncertainty or impact grows.

### Route Precedence

1. Route-away cases leave this workflow first (`systematic-debugging`,
   `requesting-code-review`, `goal-framing` when goal intent is explicit,
   fast-path micro-tasks).
2. `Grilling Mode` requires explicit challenge intent. Ordinary discussion,
   evaluation, or the need to clarify understanding is not grilling.
3. Otherwise run the normal brainstorming flow and escalate depth on evidence:
   contracts, owners, persistence, migration, security, consumer count, or
   blast radius. Escalate after evidence, not merely because the first
   request sounds ambitious.
4. File count alone is not a design signal: a mechanical multi-file change
   can still be fast-path, and a one-file contract change can still be full
   design.

## Role And Authority Contract

### Agent-owned decisions

Resolve these directly without asking the user:

- repository investigation strategy and evidence gathering order
- file and function organization inside an accepted owner
- testing commands and proportional verification mechanics
- inline versus subagent execution when policy already allows it
- reversible implementation structure that does not change product behavior,
  contract, authority, or durable boundaries

### User-owned decisions

Ask the user only for:

- product behavior or preference
- irreversible, destructive, external, public, production, or sensitive impact
- explicit product/contract commitments only the user can make
- necessary information unavailable from repository, tools, and authority docs

Every user question must pass this test:

> If the user chooses another answer, which design boundary, behavior, owner,
> acceptance criterion, or risk decision changes?

If none changes, do not ask. When a question passes this test,
attach a recommended option and the reason for it, so the user decides
between framed choices instead of researching. This classification clarifies which decisions
are user-owned; it does not remove the approval points this workflow already
defines.

## Checklist

You MUST create a task for each of these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits, authority
   docs, and passively consume relevant active `CONTEXT.md` language without
   loading active modeling
2. **Choose the path and scope** — real design? diagnosis? route accordingly or decompose first
3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
4. **Draft working artifacts** — `TaskIntentDraft`, `BaselineReadSetHint`, `BaselineUsageDraft`, `ImpactStatementDraft`
5. **Run existence check when adding new surfaces** — only if an approach adds a new owner, skill, artifact, adapter, fallback, workflow step, or benchmark metric
6. **Propose 2-3 approaches** — with trade-offs and your recommendation
7. **Present design** — in sections scaled to complexity, get user approval where required
8. **Write spec artifact** — only after the Doc Necessity Gate passes and no existing owner spec/plan covers the surface; if covered, update that document instead of creating a sibling
9. **Spec self-review** — check for placeholders, contradictions, ambiguity, scope, boundary
10. **User reviews written spec** — ask user to review before proceeding
11. **Transition to implementation** — invoke writing-plans skill (terminal state)

**The terminal state is invoking writing-plans.** Do NOT invoke any other implementation skill.

## The Process

**Understanding the idea:**
- Check current project state first (files, docs, recent commits)
- Read relevant authority docs before asking deep questions
- Use existing canonical terms in questions, options, scenarios, and the spec.
  If terminology crystallizes or conflicts, compose
  `establishing-project-context`; do not leave the resolution only in the spec.
- If the request is diagnosis/root-cause/follow-up to an approved plan → route to correct workflow
- If the request spans multiple independent subsystems → flag and decompose first
- Ask clarifying questions one at a time, prefer multiple choice
- Separate facts, assumptions, unknowns while exploring

**Working artifacts:** Keep four drafts: `TaskIntentDraft` (outcome, goal,
success evidence, stop condition, non-goals, scope, risks),
`BaselineReadSetHint` (candidate docs, authority gaps),
`BaselineUsageDraft` (required refs, optionally delivered context refs,
acknowledged-before-plan refs, cited refs, missing refs, advisory decision),
and `ImpactStatementDraft` (affected layers, owners, invariants, compat,
non-goals). Refresh when scope changes.

**Compact output contract:** `Aegis Visibility`, `TaskIntentDraft`, `BaselineReadSetHint`,
`BaselineUsageDraft`, `Requirement Ready Check`, `ImpactStatementDraft`,
`Existence Check`, `Product Risk Lens`, `Architecture Integrity Lens`,
`Prior-Art & Reuse Lens`, `Baseline Role Alignment`, `Plan-Time Complexity
Check`, `Options`, and `Decision Needed`. Use this compact shape before expanding into a full design
structure.

`Aegis Visibility` for this workflow names why design/spec clarification comes
before implementation and what drift, overbuild, wrong-owner, or missing
acceptance risk that restraint reduces. Keep it natural and task-specific; do
not turn it into a fixed skill trace.

Use a compact `BaselineUsageDraft` whenever the design direction depends on
specific baseline docs or current-authority refs:

```text
BaselineUsageDraft:
- Required baseline refs:
- Delivered context refs:
- Acknowledged before plan refs:
- Cited in design refs:
- Missing refs:
- Decision: continue | needs-baseline-readback | needs-verification | pause-for-user | blocked
```

`Delivered context refs` is optional host-projected bookkeeping only. It is not
authoritative proof that a host injected or the model internally consumed a
context payload. The artifact exists to make baseline/context attention drift
visible before the design is recommended or approved.

Use a compact `Requirement Ready Check` before recommending a design when the
requirement is not already confirmed and complete:

```text
Requirement Ready Check:
- Requirement source refs:
- Goals and scope refs:
- User / scenario refs:
- Requirement item refs:
- Acceptance / verification criteria refs:
- Open blocker questions:
- Decision: ready | needs-source | needs-goal-alignment | needs-scenario | needs-acceptance-criteria | needs-clarification | needs-user-decision | blocked
```

Treat task intent, conversation, source documents, and agent inference as
candidate requirement sources until project authority confirms them. If the
decision is not `ready`, keep the design at proposal/spec clarification level;
do not turn the gap into implementation tasks.

**Existence Check:** Before recommending an approach that adds a new owner,
skill, artifact, host adapter, fallback, compatibility path, workflow step, or
benchmark metric, check whether it needs to exist. Use
`docs/current/AEGIS_MINIMALITY_REFERENCE.md` as the reference. Do not force this
onto ordinary feature design that reuses existing owners and artifacts.

```text
Existence Check:
- Proposed new surface:
- Existing owner / reuse candidate:
- Why existing surface is insufficient:
- Creation proof:
- Entropy / retirement impact:
- Decision: reuse-existing | add-with-proof | defer | reject | needs-first-principles-review
```

If the decision is `reuse-existing`, recommend the reuse path instead of a new
surface. If the decision is `add-with-proof`, carry the proof, verification
signal, and any retirement trigger into the design/spec.

**Product Risk Lens:** For ambiguous product, feature, UI, workflow, or
architecture choices, add a compact review lens, not persona roleplay:

```text
Product Risk Lens:
- Value:
- Non-goals:
- Trade-offs:
- Decision needed:
```

This is a review lens, not persona output. It does not override baseline evidence,
approved requirements, or current authority docs; it only makes the product risk
and decision point visible before implementation.

**Plan-Time Complexity Check:** Before choosing an implementation direction for
medium/high work, inspect the likely owner files and current shape. This is an
advisory design pressure check, not a gate and not completion authority. Do not
force it onto tiny low-risk edits.

Use `using-aegis/references/complexity-governance.md` for the shared artifact
classes, pressure-signal interpretation, and over-budget handling.

```text
Complexity Budget:
- Artifact class:
- Target files / artifacts:
- Current pressure:
- Projected post-change pressure:
- Budget result: within-budget | at-risk | over-budget
- Planned governance:

Plan-Time Complexity Check:
- Better file boundary:
- Recommendation: edit-in-place | extract helper | add owner file | split task | defer refactor
```

**Exploring approaches:** Propose 2-3 approaches with trade-offs and
recommendation. Make scope boundary explicit: what's in, what's deferred, what
belongs elsewhere.

Before approach selection, use `Existence Check` for any proposed new surface.
Escalate to `first-principles-review` and its `Decision Hygiene Review` when
the candidate direction still introduces a new owner, duplicate owner,
fallback, adapter, compat-only carrier, delete-first question, unverified
assumption, or "long-term stable" claim after the existence check. Do not make
either check a universal design ceremony; return to this workflow once the
decision surface is clean.

When the central decision is internal retirement vs compat retention vs
persistent-state confirmation, compose `anti-entropy-governance`. It classifies
the deletion target, chooses `delete-first | compat-exception |
confirmation-first`, and keeps destructive authority outside the design skill.

Use the narrower `Architecture Integrity Lens` when the main risk is not broad
strategy but architecture coherence: unclear canonical owner, responsibility
overlap, caller-side fallback, stale path carrying real logic, or a possible
higher-level owner / contract / source-of-truth simplification. The lens should
answer invariant, canonical owner / contract, responsibility overlap,
higher-level simplification, retirement / falsifier, and verdict before the
approach is recommended.

**Prior-Art & Reuse Lens:** When a candidate approach would introduce a new
mechanism, protocol, artifact shape, or nontrivial interaction pattern, check
proven external practice before inventing one. This lens is behavior-triggered:
research precedents when the direction is novel for the project, plausible
approaches remain after internal reuse checks, or the domain sits outside
current repository evidence. Do not run research ceremony for routine work that
already maps to well-known framework patterns, and do not let an unavailable
web/search tool stall approach selection.

```text
Prior-Art & Reuse Lens:
- Searched precedents: <bounded sources; index-first summary; cite anchor per claim>
- Adopt verbatim: <proven pattern + source>
- Adapt with reason: <tailored part -> project constraint / non-negotiable it maps to>
- Reject with reason: <project fact that makes the pattern inapplicable>
- Degraded: <no web/search tooling -> external basis unknown; internal-only evidence stated>
```

Search results are evidence candidates, not prompt payload: summarize
index-first and cite anchors instead of pasting raw pages. An "industry
standard" claim without a citable anchor stays `unknown`. Every adapt/reject
decision binds to a named project constraint or fact, not taste. The lens feeds
only the approach recommendation; it stays advisory and grants no completion
authority.

**Baseline Role Alignment:** When a question may involve both "what should be
built" and "where it should live", keep requirement truth separate from
architecture truth:

```text
Baseline Role Alignment:
- Product / Requirement Baseline:
- Architecture / Runtime Boundary Baseline:
- Result: aligned | Design Defect | Implementation Drift | missing-authority | needs-clarification
- scope: requirements | architecture | both
- Next action:
```

Use `Design Defect` when the relevant requirement, design, or baseline is wrong.
Use `Implementation Drift` when the work deviates from a correct unchanged
baseline. `Architecture Defect` and `Architecture Drift` remain compatibility
aliases for architecture-scoped `Design Defect` and architecture-scoped
`Implementation Drift`. This is a review lens, not a runtime gate or completion
authority.

**Presenting the design:** Scale sections to complexity. Cover only the surfaces that matter: architecture, components, data flow, error handling, testing, compatibility boundary. Get approval for the design before implementation when behavior, contract, architecture, or user-facing flow is being decided.

**ADR signals:** When the design/spec touches durable architecture surfaces
(owner, public contract, artifact shape, dependency direction,
source-of-truth, host compatibility, runtime-ready boundary, fallback,
adapter, or retirement schedule), mark the ADR signal, source refs, real
alternatives, and expected baseline-sync question for later completion. Do not
create accepted architecture memory from unexecuted ideas.

**Design for isolation:** Each unit = one clear purpose, well-defined interface, testable independently. Can someone understand it without reading internals? Can you change internals without breaking consumers?

**Existing codebases:** Follow existing patterns. Include targeted improvements only when they serve the current goal. If the design touches contracts, compat, fallbacks, or duplicated owners → call it out directly.

## Design Probe

A probe is allowed only when it can change the design direction and existing
repository evidence is insufficient:

```text
Design Probe
- Question
- Expected decision impact
- Target and effect boundary
- Why existing evidence is insufficient
- Stop condition
- Evidence produced
- Cleanup
```

Prefer read-only execution. A disposable probe must not create a maintained
owner, public contract, compatibility promise, or hidden persistence path. It
is design evidence, not delivered implementation.

## Software Scenario Profiles

Apply only the relevant profile instead of loading every lens for every task:

- `greenfield-feature`: value, smallest deliverable behavior, minimum owner,
  acceptance, explicit future non-goals;
- `existing-system-change`: current state, target state, the delta between
  them, preserved invariants, callers, migration, and retirement;
- `refactor`: preserved observable behavior, owner/coupling defect, dependency
  direction, old-path retirement, behavior-preservation evidence;
- `public-contract`: consumers, versioning, precedence, errors, compatibility,
  migration, negative cases;
- `persistence-migration`: data owner, schema evolution, partial migration,
  crash recovery, backup/rollback, read/write cutover;
- `ui-workflow`: user journey and loading/empty/error/partial/success/cancel/
  retry states, accessibility, irreversible actions, recovery;
- `security-permission`: trust boundary, attacker capability, authority owner,
  sensitive data, downgrade/revocation, safe failure, auditability;
- `operational-release`: deployment boundary, observability, partial rollout,
  rollback, compatibility window, operator recovery.

## Design Ready And Design Complete

Approach selection is ready when:

- the desired outcome and primary scenario are known;
- scope and non-goals are explicit;
- current behavior and the target delta are grounded;
- key invariants and the likely canonical owner are identified;
- at least one observable acceptance criterion exists;
- no open unknown can still change the approach category.

Not every unknown must be eliminated; only decision-changing unknowns block
convergence.

The design can hand off when all applicable conditions hold:

- the selected approach and canonical owner are explicit;
- fixed behavior/contract and implementation-owned choices are separated;
- alternatives were materially compared or excluded by evidence;
- critical assumptions have evidence or explicit acceptance;
- failure/recovery and consumer impact are covered where applicable;
- acceptance criteria are observable and usable by verification;
- new owners, fallbacks, adapters, compatibility, or persistence have creation
  proof and retirement/rollback treatment;
- every user-owned decision has real user approval.

Design Complete is method readiness, not completion authority. Transition to
writing-plans only after these conditions hold; do not carry unresolved
decision-changing unknowns into the plan.

## After the Design

**Documentation:**

1. **Aegis Project Workspace initialization (first creation only):**
   If `docs/aegis/` does not exist and configured Aegis workspace support is
   available, initialize the target project:
   `python <aegis-workspace-helper> init --root <target-project-root>`.
   If installed Aegis workspace support is unavailable, create it manually:
   a. Create `docs/aegis/README.md` — describes workspace purpose and structure
   b. Create `docs/aegis/INDEX.md` — empty index, will be appended below
   c. Create `docs/aegis/BASELINE-GOVERNANCE.md` from the template in
      "BASELINE-GOVERNANCE.md Template" section below
   d. If the project has existing code, create an initial baseline snapshot:
      `docs/aegis/baseline/YYYY-MM-DD-initial-baseline.md` using the
      "Initial Baseline Snapshot Template" below
   If `docs/aegis/` already exists, use it — do not recreate.

2. **Write the validated spec artifact when needed:**
   Use the smallest artifact that stabilizes the task:
   - Spec Brief: `docs/aegis/specs/YYYY-MM-DD-<topic>-brief.md` for medium
     tasks that need what/why/acceptance pinned before planning.
   - Design Spec: `docs/aegis/specs/YYYY-MM-DD-<topic>-design.md` for high
     complexity, architecture, contract, migration, cross-module, or ambiguous
     behavior requiring user review.
   Specs always go to `specs/` — never to `work/`. `docs/aegis/work/`
   holds session-level drafts, not project documents; only promote a draft to
   `specs/` or `plans/` when the Doc Necessity Gate passes.

3. **Update INDEX.md:**
   Prefer configured Aegis workspace support: `python <aegis-workspace-helper> append-index --root
   <target-project-root> --path docs/aegis/specs/<filename>.md --kind spec
   --title "<title>"`. If workspace support is unavailable, append the new spec entry
   to `docs/aegis/INDEX.md` manually.
   After the append, run `python <aegis-workspace-helper> check --root
   <target-project-root>` when configured workspace support is available. This validates
   structure and index coverage only; it does not grant completion authority.
   INDEX bookkeeping: creating a document registers it; updating an existing
   document does not change the index; superseding or deleting a document
   updates the index.

4. Commit the design document to git.

5. Include the latest `TaskIntentDraft`, `BaselineReadSetHint`,
   `BaselineUsageDraft`, and `ImpactStatementDraft` inline or in an appendix
   when they materially shaped the design.

6. Record explicit non-goals and compatibility boundaries so the later implementation plan does not drift.
7. Cross-repo changes: decide per change surface per repo; a durable
   cross-repo contract is recorded as an ADR in the owning repo, with the other
   side carrying only its local impact (mirror relationship, no duplication).

**Spec Self-Review:**
After writing the spec document, look at it with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
5. **Boundary check:** Did you clearly mark invariants, compatibility
   boundaries, owners, non-goals, and any ADR signals for later completion
   backfill? If the spec endorses a risky approach, confirm the
   `first-principles-review` `Decision Hygiene Review` or `Architecture
   Integrity Lens` result is reflected or explicitly marked unnecessary.

Fix any issues inline. No need to re-review — just fix and move on.

**User Review Gate:**
After a Design Spec review loop passes, ask the user to review the written spec before proceeding:

> "Spec written and committed to `<path>`. Please review it and let me know if you want to make any changes before we start writing out the implementation plan."

Wait for the user's response when this workflow requires review. If they request changes, make them and re-run the spec review loop. Only proceed once the user approves. For a small Spec Brief created only to pin medium-task acceptance, user review may be concise unless project rules require a formal approval step.

**Implementation:**

- Invoke the writing-plans skill to create a detailed implementation plan
- Do NOT invoke any other skill. writing-plans is the next step.

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design, get approval before moving on
- **Be flexible** - Go back and clarify when something doesn't make sense

## BASELINE-GOVERNANCE.md Template

When creating `docs/aegis/BASELINE-GOVERNANCE.md` for the first time, use this template:

```markdown
# Baseline Governance

## 1. Baseline Roles
- Product / Requirement Baseline: confirmed requirement sources, target state,
  goals and scope, users / scenarios, requirement items, acceptance /
  verification criteria, non-goals, workflow constraints, open questions,
  change records, and approved requirement/spec intent.
- Architecture / Runtime Boundary Baseline: canonical owner, contract,
  source-of-truth boundary, dependency direction, compatibility, runtime-ready
  boundary, and retirement state.

## 2. Design Defect
A confirmed error, gap, contradiction, or wrong abstraction IN the relevant
requirement, design, or baseline.
- Fix the defective requirement/design/baseline first.
- Then align implementation to the corrected baseline.
- Do NOT patch implementation around a defective baseline.

## 3. Implementation Drift
Implementation, plan, review, or documentation has deviated from a confirmed,
correct, unchanged requirement or architecture baseline.
- Return to baseline via the simplest stable path.
- Do NOT "update baseline to match drift" without explicit review.

## 4. Compatibility Aliases
- Architecture Defect = architecture-scoped Design Defect.
- Architecture Drift = architecture-scoped Implementation Drift.
- New findings should report Design Defect / Implementation Drift plus
  `scope: requirements | architecture | both`.

## 5. Baseline Check Protocol
Before non-trivial changes:
1. Read the latest Product / Requirement Baseline candidate.
2. Read the latest Architecture / Runtime Boundary Baseline candidate.
3. Compare current work against requirement acceptance and architecture owner /
   contract boundaries.
4. Check for new anti-patterns not recorded in known list.
5. Report: aligned / Design Defect / Implementation Drift /
   missing-authority / needs-clarification, with
   `scope: requirements | architecture | both`.

## 6. Architecture Review — 7 Dimensions
After each non-trivial change:
1. **Ownership integrity** — every component has exactly one canonical owner
2. **Module boundaries** — no unauthorized cross-module coupling
3. **Contract changes** — all API/signature/behavior contract changes documented
4. **Cascade proliferation** — no new cascading dependency chains
5. **Dependency direction** — dependencies flow toward stability
6. **Retirement completeness** — old owners/fallbacks/paths removed or scheduled
7. **Entropy flow** — net complexity decreased or stayed; no unjustified new entities

## 7. Hard Boundaries
- BASELINE-GOVERNANCE.md is the constitution for THIS project's Aegis workspace
- Baseline snapshots in `baseline/` are evidence, not authority
- ADRs in `adr/` record decisions; they do not replace baseline governance
- This file is NEVER auto-updated — changes require explicit user review
```

## Initial Baseline Snapshot Template

When creating the first `docs/aegis/baseline/YYYY-MM-DD-initial-baseline.md`:

Bootstrap the project's dual baselines instead of writing a flat repo inventory.
The first baseline should make later `Baseline Role Alignment` checks possible
even when the repo is still early or partially defined.

Minimum shape:

```markdown
# <Project> Initial Baseline

Date: `YYYY-MM-DD`
Status: `initial dual-baseline snapshot`

## 1. Purpose
- why this baseline exists
- what later alignment checks should use it for

## 2. Workspace Structure
- top-level directories, entry points, substrate roots, or seams worth tracking

## 3. Current Authority Surfaces
- README / AGENTS / ADR / spec / baseline / external reference roots
- current authority gaps or missing documents

## 4. Product / Requirement Baseline
### 4.1 Current Truth
- confirmed requirement sources or current authority gaps
- target state, goals, and scope
- target users, roles, usage scenarios, or system scenarios
- functional, quality, constraint, and delivery / transition requirement items
- acceptance / verification criteria and evidence expectations
- success evidence, value claim, or phase focus already fixed

### 4.2 Non-negotiables
1. ...

### 4.3 Product Non-goals
- ...

## 5. Architecture / Runtime Boundary Baseline
### 5.1 Current Truth
- canonical owner or substrate split
- contract / source-of-truth boundary
- dependency direction or owner layering already fixed

### 5.2 Architecture Non-negotiables
1. ...

### 5.3 Architecture Non-goals
- ...

## 6. Ownership / Contract Snapshot
- important surface -> current owner
- contract seams, missing seam inventory, or boundary gaps

## 7. Current State and Risks
- current stage
- known risks, unknowns, or missing evidence

## 8. Alignment Use
- when to read the Product / Requirement Baseline
- when to read the Architecture / Runtime Boundary Baseline
- when to report `scope: both`

## 9. Compatibility Boundary
- what must NOT break during early work
```

Do not collapse the first bootstrap baseline into a generic 10-field checklist.
If the project is sparse, keep sections short and mark authority gaps explicitly
instead of guessing.
