# Expanded Design Guidance

This reference carries conditional design detail for `brainstorming`.
It does not own routing. It also does not own the no-implementation gate,
approval, or completion authority.
Read only the section activated by current task evidence:

- `Design Probe` when repository evidence is insufficient and a bounded probe
  can change the design direction.
- `Software Scenario Profiles` after the relevant scenario class is known.
- `Documentation And Workspace Bootstrap` only after the Doc Necessity Gate
  selects a spec or project workspace artifact.

Do not load this file for route selection, first-turn clarification, route-away
cases, or an active Grilling Mode interview.

## Contents

- Design Probe
- Software Scenario Profiles
- Documentation And Workspace Bootstrap
- Spec Self-Review
- BASELINE-GOVERNANCE.md Template
- Initial Baseline Snapshot Template

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

## Documentation And Workspace Bootstrap

Use this section only after the main skill's Doc Necessity Gate selects a
durable artifact.

1. For first workspace creation, prefer configured Aegis workspace support:

   ```bash
   python <aegis-workspace-helper> init --root <target-project-root>
   ```

   If support is unavailable, create `docs/aegis/README.md`,
   `docs/aegis/INDEX.md`, and `docs/aegis/BASELINE-GOVERNANCE.md` from the
   template below. For an existing project, also create
   `docs/aegis/baseline/YYYY-MM-DD-initial-baseline.md` from the initial
   snapshot template. Reuse an existing `docs/aegis/`; never recreate it.

2. Write the smallest validated spec artifact that stabilizes the task:

   - Spec Brief: `docs/aegis/specs/YYYY-MM-DD-<topic>-brief.md` for medium work
     that needs what/why/acceptance pinned before planning.
   - Design Spec: `docs/aegis/specs/YYYY-MM-DD-<topic>-design.md` for high
     complexity, architecture, contract, migration, cross-module, or ambiguous
     behavior requiring user review.

   Specs belong in `specs/`, never `work/`. Promote session drafts only after
   the Doc Necessity Gate passes.

3. Register a newly created spec, then validate workspace structure:

   ```bash
   python <aegis-workspace-helper> append-index --root <target-project-root> --path docs/aegis/specs/<filename>.md --kind spec --title "<title>"
   python <aegis-workspace-helper> check --root <target-project-root>
   ```

   If workspace support is unavailable, append the entry manually. Updating an
   existing document does not add another index entry; superseding or deleting
   one updates the index. Structural validation does not grant completion
   authority.

4. Commit the validated design document. Include the latest
   `TaskIntentDraft`, `BaselineReadSetHint`, `BaselineUsageDraft`, and
   `ImpactStatementDraft` only when they materially shaped it.

5. Record explicit non-goals and compatibility boundaries. For cross-repo
   change surfaces, keep the durable contract ADR in its owning repository and
   carry only local impact elsewhere.

## Spec Self-Review

Before user review, fix these inline:

1. placeholders or vague requirements;
2. internal contradictions;
3. scope too broad for one implementation plan;
4. requirements with multiple plausible interpretations;
5. missing invariants, compatibility boundaries, owners, non-goals, ADR
   signals, or applicable first-principles findings.

## BASELINE-GOVERNANCE.md Template

When manual workspace bootstrap is required, use this template:

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

Bootstrap dual baselines instead of a flat repository inventory. Keep sections
short and mark authority gaps explicitly when the project is sparse.

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
- target state, goals, scope, users, scenarios, and requirement items
- acceptance / verification criteria and evidence expectations

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
- when to read each baseline role
- when to report `scope: both`

## 9. Compatibility Boundary
- what must NOT break during early work
```

Do not collapse this bootstrap into a generic checklist.
