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

Choose the route before reading references:

1. Tiny wording edits, simple Q&A/status, local utility or mechanical changes
   stay on the fast path. Bugs/diagnosis use `systematic-debugging`; PR, diff,
   or current-code review uses `requesting-code-review`; explicit goal framing
   uses `goal-framing`. File count alone does not decide design complexity.
2. Direct interview requests use `Grilling Mode` below; soft challenge intent
   requires its one-line mode confirmation. Ordinary evaluation is not grilling.
3. Ambiguous or medium/high-complexity feature, product, UI, architecture or
   contract design follows `Default Design Path`. Escalate depth from evidence:
   contracts, owners, persistence, migration, security, consumers and blast radius.

<HARD-GATE>
Do NOT write code, scaffold projects, or invoke implementation skills until the
needed design/spec approval is satisfied. Existing approval satisfies unchanged
decisions; clarify only decision-changing gaps. Grilling never authorizes
implementation or normal design artifacts while the interview is active.
</HARD-GATE>

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

## Grilling Mode

### Grilling Entry Signals

- **Direct:** `grill me`, `grill this plan`, `审问我`, `盘问我`, `拷问我`, or an
  explicit request to interrogate/pressure-test a plan enters this mode.
- **Soft:** challenge assumptions, find holes, red-team, or "别顺着我" without
  explicit interview intent: ask only `Grill or normal brainstorming?` and
  enter only after confirmation.
- **Not grilling:** literal phrase explanations stay explanatory; PR, diff, or current-code review routes to `requesting-code-review`.

Grilling Mode overrides the normal brainstorming execution flow. Suspend the
Default Design Path, compact output contract, and documentation or planning
requirements until the user exits the interview; retain the no-implementation
gate. Only after entry, read `grilling-mode-reference.md` for interview pace,
opening, questions and exit procedure. Do not read it for ordinary design,
soft-intent confirmation, or literal phrase explanations.
Stop the interview when the user says stop, defer, or that questions are
sufficient. Its summary does not authorize planning or implementation; return
to the normal design approval gate if the user asks to proceed.

## Default Design Path

Track the applicable steps in order; conditional steps do not create tasks or
artifacts until their trigger is met. Keep one workflow, not separate checklist,
process and after-design passes.

1. **Ground the request.** Inspect current files, relevant authority docs and
   recent changes. Passively use active `CONTEXT.md`/`CONTEXT-MAP.md` terms;
   compose `establishing-project-context` only for a real semantic conflict.
   Decompose independent subsystems before designing them. Define the user's
   usable result, delivery and meaningful failure states; an unsupported action
   remains an unmet need, not a reason to silently narrow the requirement.
2. **Clarify decision-changing gaps.** Follow the authority contract below.
   Ask one question at a time, preferably with choices and a recommendation.
   Reuse answers and approvals; do not ask the user for repository facts.
3. **Frame scope and alternatives.** Maintain the working drafts below, propose
   2-3 approaches with trade-offs and a recommendation, and say what is in,
   deferred or owned elsewhere. Apply only evidence-triggered checks from the
   conditional table before recommending the approach.
4. **Present the design.** Scale sections to complexity: affected architecture,
   components/data flow, failure/recovery, consumers, compatibility and testing.
   Follow existing patterns; keep each unit cohesive and testable, and remove
   unnecessary features. Obtain required approval for each applicable design
   section before proceeding; return to clarification when evidence changes it.
5. **Persist only when needed.** Apply the Doc Necessity Gate. For a written
   Design Spec, load the self-review section, fix placeholders, contradictions,
   ambiguity, scope and boundary defects, then obtain user review. A small Spec
   Brief may use concise review unless project authority requires a formal gate.
6. **Hand off only when ready.** Check Design Ready And Design Complete below;
   preserve ADR signals for durable owner/contract/schema/dependency/compatibility/
   runtime-boundary changes, including source refs, alternatives and baseline-sync
   questions. Do not create accepted architecture memory from unexecuted ideas.
   The terminal state is invoking `writing-plans`, not another implementation
   skill. For a scope ending at discussion or options, deliver that result;
   do not advance beyond the user's request.

## Compact output contract

Use natural, proportional prose, not a mandatory stack of named cards.
`Aegis Visibility` briefly explains the task-specific value of design first.
Keep these working drafts current as scope changes; they are in-session views
unless the Doc Necessity Gate requires persistence:

- `TaskIntentDraft`: outcome, goal, success evidence, stop condition, non-goals,
  scope and risks;
- `BaselineReadSetHint`: candidate authority refs and gaps;
- `BaselineUsageDraft`: required, delivered-context (optional), acknowledged,
  cited and missing refs, plus the advisory decision;
- `ImpactStatementDraft`: affected layers, owners, invariants, compatibility
  and non-goals.

Present the relevant intent, evidence, impact, options and decision needed at
this stage. Conditional lenses below add only their applicable findings;
mentioning a lens does not activate its template. Do not repeat satisfied checks
or emit empty cards. Preserve decision-relevant meaning and evidence limits.

## Doc Necessity Gate

Before writing any spec, plan, ADR or baseline artifact:

1. If an existing spec/plan/ADR/baseline owns this surface, update it in place;
   never create a sibling owner.
2. Write the smallest artifact only for a durable/irreversible surface (schema,
   public API, owner, dependency, migration, compatibility retirement), cross-session/
   cross-person handoff, or an approval/authority requirement. Otherwise keep
   compact drafts in-session and write no document.
3. Re-check at edit time and closeout; expand only if uncertainty or impact grows.
   Workspace creation and spec persistence follow project authority. Read the
   workspace/bootstrap reference only after selecting a durable artifact.

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

## Conditional Detailed Guidance

For design detail, read only the evidence-matched heading of
`expanded-design-guidance.md`, never the whole file. Do not load design detail
for route selection, first-turn clarification, route-away cases, or an active
Grilling Mode interview. The main file owns routing, approval and handoff;
references supply the selected procedure or template only.

| Evidence trigger | Exact section to read / action |
| --- | --- |
| Repository evidence is insufficient and a bounded probe can change the approach | `## Design Probe` |
| The software scenario class is known and its domain risks matter | `## Software Scenario Profiles`; use only the relevant profile |
| Doc Necessity Gate selects a spec/workspace artifact | `## Documentation And Workspace Bootstrap`; a named baseline template only when initializing that exact file |
| A written Design Spec is ready for review | `## Spec Self-Review` |
| A baseline-dependent recommendation needs structured usage evidence | `### Baseline Usage Draft` under `## Design Artifact Templates` |
| Requirements, scenarios or acceptance remain incomplete or disputed before a design recommendation | `### Requirement Ready Check`; stay at proposal/spec clarification until decision-changing gaps are resolved |
| An approach introduces an owner, skill, artifact, adapter, fallback, compatibility path, workflow step or metric | `### Existence Check`; reuse the existing owner when sufficient |
| Ambiguous product, feature, workflow or architecture choices | `### Product Risk Lens`; keep value, non-goals, trade-offs and the decision compact |
| Choosing a medium/high-complexity implementation direction | `### Plan-Time Complexity Check And Complexity Budget`; inspect actual owners/file shape before choosing |
| Novel mechanism, protocol, artifact or interaction; unresolved alternatives after internal reuse checks; domain outside repository evidence | `### Prior-Art And Reuse Lens` (Prior-Art & Reuse Lens); routine established patterns need no external research ceremony |
| Both what to build and where it belongs are at issue | `### Baseline Role Alignment`; distinguish requirement truth from architecture truth |

Before approach selection, unresolved new/duplicate owners, fallback, adapter,
compat-only carrier, delete-first questions, unverified assumptions or a
"long-term stable" claim after Existence Check escalate to
`first-principles-review` and its `Decision Hygiene Review`; return here once
that decision surface is clean. Do not make this a universal design ceremony.

For narrower architecture coherence risks, use `Architecture Integrity Lens`:
invariant, canonical owner/contract, responsibility overlap, higher-level
simplification, retirement/falsifier and verdict. For internal retirement vs
compatibility retention vs persistent-state confirmation, compose `anti-entropy-governance`;
it chooses `delete-first | compat-exception | confirmation-first` without
transferring destructive authority to this skill.

For user-facing interface or interaction design, compose `ui-ux-governance` and
carry scoped experience rules into existing acceptance criteria. Design approval
and handoff remain here.

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
