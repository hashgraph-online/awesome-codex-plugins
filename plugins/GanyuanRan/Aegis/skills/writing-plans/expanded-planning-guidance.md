# Expanded Planning Guidance

This reference contains conditional planning detail. It does not own routing,
plan-versus-Planless selection, implementation authorization, or completion.
Load it only through a trigger in `SKILL.md`; emit only the triggered structures.

## Contents

1. [Workspace Save Detail](#workspace-save-detail)
2. [Baseline And Requirement Detail](#baseline-and-requirement-detail)
3. [New-Surface And Architecture Detail](#new-surface-and-architecture-detail)
4. [Complexity Detail](#complexity-detail)
5. [Execution Readiness Detail](#execution-readiness-detail)
6. [Execution Route Detail](#execution-route-detail)
7. [Expanded Plan Review](#expanded-plan-review)

## Workspace Save Detail

Initialize an absent target-project workspace only when project authority
permits it and the durable plan save requires it:

```bash
python <aegis-workspace-helper> init --root <target-project-root>
```

If installed workspace support is unavailable, create `docs/aegis/README.md`,
`docs/aegis/INDEX.md`, the governed baseline file, and an initial baseline for
an existing codebase. Do not create this live workspace inside the Aegis Method
Pack repository.

Save the plan under `docs/aegis/plans/`, then register a newly created plan and
check structure:

```bash
python <aegis-workspace-helper> append-index --root <target-project-root> --path docs/aegis/plans/<filename>.md --kind plan --title "<title>"
python <aegis-workspace-helper> check --root <target-project-root>
```

Updating an existing document does not add a second index row. Workspace checks
prove structure and index coverage, not plan correctness or completion.

## Baseline And Requirement Detail

Use this only when named baseline/context acknowledgement matters:

```text
BaselineUsageDraft:
- Required baseline refs:
- Delivered context refs:
- Acknowledged before plan refs:
- Cited in plan refs:
- Missing refs:
- Decision: continue | needs-baseline-readback | needs-verification | pause-for-user | blocked
```

`Delivered context refs` is host-projected bookkeeping, not proof that a host
injected content or that a model consumed it.

Use the expanded readiness form when acceptance is incomplete or disputed:

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

Any result other than `ready` blocks implementation tasks and returns the
smallest missing evidence or decision to its owner. Conversation or agent
inference may be candidate evidence, not durable authority by itself.

When an auditable code-necessity record is needed:

```text
Change Necessity:
- User-visible need:
- No-change / non-code option:
- Why code change is necessary:
- Minimum change boundary:
- Decision: no-change | docs/config-only | code-change | needs-clarification
```

## New-Surface And Architecture Detail

Use for a proposed new owner, skill, artifact, adapter, fallback,
compatibility path, workflow step, or benchmark metric:

```text
Existence Check:
- Proposed new surface:
- Existing owner / reuse candidate:
- Why existing surface is insufficient:
- Creation proof:
- Entropy / retirement impact:
- Decision: reuse-existing | add-with-proof | defer | reject | needs-first-principles-review
```

`reuse-existing` redirects tasks to the current owner. `add-with-proof` carries
the proof, verification signal, and retirement effect into the task.

An expanded `Architecture Integrity Lens` records the invariant, canonical
owner/contract, responsibility overlap, possible higher-level simplification,
old-path retirement or falsifier, and verdict. Use
`first-principles-review` before task decomposition when direction risk remains.

Use an expanded pressure record only when natural plan prose is insufficient:

```text
Plan Pressure Test:
- Owner / contract / retirement:
- Architecture integrity / higher-level path:
- Verification scope:
- Task executability:
- Pressure result: proceed | revise plan | return to design
```

## Complexity Detail

Use `using-aegis/references/complexity-governance.md` for shared artifact
classes, pressure signals, and over-budget handling.

```text
Complexity Budget:
- Artifact class:
- Target files / artifacts:
- Current pressure:
- Projected post-change pressure:
- Budget result: within-budget | at-risk | over-budget
- Planned governance:

Plan-Time Complexity Check:
- Target files:
- Existing size / shape signals:
- Owner fit:
- Add-in-place risk:
- Better file boundary:
- Recommendation: edit-in-place | extract helper | add owner file | split task | defer refactor
```

An `over-budget` result cannot be hidden inside an add-in-place task. Change the
boundary, add governance work, or explicitly stop for follow-up.

## Execution Readiness Detail

Use existing plan inputs; do not create a new JSON artifact type:

```text
Execution Readiness View:
- Intent Lock:
- Scope Fence:
- Baseline Lock:
- Approved Behavior:
- Owner / Contract Constraints:
- Compatibility Boundary:
- Retirement Boundary:
- Task Batches:
- Test Obligations:
- Review Gates:
- Drift / Rewind Rules:
- Evidence Required Before Completion:
- Advisory Boundary: method-pack execution guidance only; not GateDecision, PolicySnapshot, or completion authority
```

This is a handoff projection, not evidence that the work passed and not an
approval gate. Skip it for tiny fast-path tasks unless explicitly requested.

## Execution Route Detail

Use only when route evidence needs structured handoff:

```text
Execution Route:
- Decision: subagent-driven | inline
- Evidence:
- Fallback:
- User confirmation required: no | yes — <specific unresolved boundary>
```

Subagent availability alone does not select delegation. Unknown dependencies,
shared transactions/resources, stale state, untrusted inputs, unclear host
capability, or borderline coordination value remain inline.

## Expanded Plan Review

For a high-risk or handoff-heavy plan, verify:

- every approved requirement and acceptance example maps to a task and check;
- paths, owners, signatures, and command outcomes are concrete enough to act;
- compatibility, rollback, repair, and retirement surfaces are explicit;
- new surfaces have creation proof and no duplicate owner;
- complexity and execution-readiness triggers have dispositions;
- ADR signals and baseline-sync questions remain available to completion; and
- no placeholder, speculative contract, or unapproved scope growth remains.

Use `plan-document-reviewer-prompt.md` only when an independent plan review is
actually dispatched. Its reviewer output is advisory and cannot authorize
implementation or completion.
