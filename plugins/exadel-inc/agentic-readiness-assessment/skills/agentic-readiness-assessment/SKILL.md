---
name: agentic-readiness-assessment
description: >
  Evaluates a software repository for readiness to be developed and maintained
  by AI coding agents, and produces an evidence-based readiness scorecard. Use
  when the user requests an agentic-readiness assessment, readiness scorecard,
  AI-readiness audit of a codebase, or recommendations for improving
  AI-assisted development workflows.
license: Apache-2.0
---

# Agentic Readiness Assessment

Read the `version` field of the plugin's `plugin.json` and record it as `prompt_version` in the report run block, so reports produced by different revisions stay comparable. Write `unknown` if the manifest cannot be read.

## Objective

Assess whether an AI coding agent can independently understand this repository, find the correct change points, establish a reproducible environment, validate work, and prepare a change for delivery. Produce an evidence-backed improvement backlog for maintainers.

This is an audit. Do not implement features or refactor production code. Create only one file: `reports/agentic-readiness.md`, a single document holding both the decision content and the supporting evidence.

The only permitted change to any other tracked file is the single reversible probe edit described in *Probe*, which you revert before writing the report. Preserve all pre-existing user changes.

The deliverable of this task is that report. Any standing instruction to output only code, or to treat an analysis document as a failed task, applies to feature work and not to this audit.

## Host Execution Contract

Read `references/agent-execution-contract.md` before collecting the baseline. Under the explicit constraints in Run and Scope, record the host's model identity, effective permission profile, command boundary, run stop condition, and context telemetry availability. Write `unavailable` for any field the host cannot evidence, classify it as an `agent-environment` limitation, and never invent a tool restriction, model pin, or telemetry control. After roughly five attempts to obtain unavailable evidence, stop and record the limitation.

## Evidence and Safety Rules

1. Cite repository-relative paths and line numbers for repository claims.
2. Cover every applicable workspace or component; do not silently sample a monorepo.
3. Prefer commands from agent instructions, documentation, task runners, package scripts, and CI. Label each command `documented` or `inferred`.
4. Run relevant safe commands. Record exact commands, working directories, results, durations when measured, and artifacts.
5. A command you did not execute is a claim, not evidence. Do not mark a capability verified because configuration exists when a safe executable check was available. A reachable health endpoint does not prove the system behind it performs meaningful work.
6. Do not deploy, publish, push, run production migrations, use real credentials or customer data, call paid services, or execute destructive or privileged commands.
7. Never bulk-restore. Do not run `git restore`, `git checkout -- .`, `git clean`, or `git reset` across the tree. Revert the probe by rewriting the exact path you edited.
8. Stop only services you started, and delete only artifacts you created. Never create, update, or commit a lockfile or equivalent resolution data.
9. Run linters and formatters in check or diff mode. Never auto-fix.
10. Use reasonable timeouts. Leave no background processes running.
11. Write `Not found` when evidence is absent. Never infer a capability, and never reinterpret a failure as a pass.

**Never let your own tooling become the finding.** If a command fails because of a flag you chose, a wrapper you lack, a missing timing utility, or a typo, retry it correctly and log only the meaningful attempt. Offline, cached-only, or sandbox-restricted flags are your constraints, not the repository's — a failure they cause is never evidence against the repository.

Classify commands before execution:

- **local-read:** Reads repository or machine state. Run.
- **local-build:** Produces local build, cache, test, or ignored artifacts. Run when documented and safe.
- **external-read:** Reads from a registry or source already required by the repository. Run only when permitted; record the endpoint.
- **external-write:** Pushes, publishes, deploys, or mutates remote state. Do not run.
- **privileged:** Requires root, `sudo`, or machine-wide changes. Do not run.
- **paid:** Calls a billed external service. Do not run.

Run `python3 <skill-directory>/scripts/validate_report.py reports/agentic-readiness.md` from the audited repository after the provisional report write; `<skill-directory>` is the directory containing this `SKILL.md`, not a path inside the audited repository. This is a `local-read` command that validates the report contract without changing the repository.

Being documented does not make a command safe. A refused command is not a skipped category: record it, name its class, and score on the safe evidence that remains.

### Dependency Installation

Attempt the repository's frozen or locked installation first, in the ecosystem's own idiom. If it fails because resolution data is missing, incomplete, or incorrect, that is a repository finding — record it, then retry **once** with the ecosystem's non-frozen install using flags that cannot create or modify resolution files, for example `npm install --package-lock=false`.

Label that result **unfrozen fallback**. Evidence obtained after a successful fallback is valid for every downstream area: proving that typecheck, tests, and the build actually pass is more useful than reporting them unproven. The setup area itself scores at most half when the fallback was required. If even the fallback fails, or if the ecosystem offers no non-mutating equivalent, record the blocker and move on.

## Blockers and Fix Ownership

Keep repository readiness separate from limitations of the audit environment:

- **Repository blocker:** Repository-owned instructions, dependencies, commands, fixtures, or controls are missing, incorrect, unsafe, contradictory, or nondeterministic.
- **Environment blocker:** The repository documents a sufficient requirement, but the audit machine lacks the required tool, service, network access, or permission.
- **External prerequisite:** A credential or external service is required; assess whether a documented local or test substitute exists.
- **N/A:** The capability is genuinely irrelevant to the repository archetype.

Route each fix to one owner:

- **repo:** A file or control in the audited repository.
- **agent-environment:** The image, hook, runtime, or toolchain that hosts the coding agent.
- **platform:** Organization or infrastructure configuration outside both the repository and agent environment.
- **external-service:** A third-party service, credential, or policy outside local control.

A missing build tool is never a documentation fix. If `make`, a container runtime, a package manager, or a browser is absent, the owner is `agent-environment`; documenting the prerequisite instead is a deferred repair. Missing prerequisite documentation is itself a separate repository defect.

Do not invent an external file path or configuration key. If the exact target cannot be established, name the required artifact generically and mark the target unverified.

## Audit Method

### Delegation

Read `references/assessment-decision-record.md` before baseline collection. Use the audit agent only to interpret repository evidence; use deterministic commands for score arithmetic and `scripts/validate_report.py` for report validation. The requesting human owns scope constraints and must approve an irreversible operation before it runs; otherwise stop and record the command as refused. Keep the delegation map's Cost / Complexity / Risk discipline in the evidence and report the named detection mechanism for any limitation.

### 1. Baseline and Scope

Capture the baseline before anything else: tracked and untracked worktree state, stash list, commit, and branch. A dirty tree or pre-existing untracked directory is the baseline, not an error. Record the platform, explicit constraints, and relevant installed tools.

Classify the repository as an application, service, frontend, library, CLI, infrastructure, documentation, data pipeline, monorepo, or an applicable combination. List all components and workspaces in scope.

### 2. Resolve the Archetype's Surfaces

Before scoring, name the concrete command filling each role, or `N/A` with justification.

| Role | Application / service | Library / SDK | Infrastructure | Documentation | Data / model |
|---|---|---|---|---|---|
| Deliverable | Build the app or image | Package or compile | Validate or lint the plan | Render the site | Build the pipeline or compile the schema |
| Primary verification | Unit or component tests | Unit tests, API compatibility | Policy or conformance tests | Link, schema, front-matter checks | Schema validation, golden-record tests |

If a role is `N/A`, name the nearest executable substitute and say what it does not prove. A repository with no executable verification surface at all cannot be Ready.

### 3. Reconstruct the Golden Path

Determine the intended route from a clean checkout to a delivered change:

`setup -> targeted feedback -> full validation -> review or PR`

Inspect:

- `AGENTS.md`, `CLAUDE.md`, repository-local rules, commands, prompts, and skills;
- README, architecture, contribution, ownership, and delivery documentation;
- manifests, dependency-resolution files, runtime versions, environment examples, containers, and fixtures;
- task runners, build scripts, test configuration, hooks, permission and policy files, and CI.

Trace one representative feature from its entry point through business logic, persistence or an external boundary, UI when applicable, and tests. Assess whether a newcomer can discover where a similar change and its tests belong. Do not edit the feature.

### 4. Exercise Applicable Validation

For every component, find and safely exercise the applicable surfaces: dependency bootstrap; build, packaging, rendering, or schema validation; static analysis; unit tests; integration or contract tests; runtime, API, CLI, or local-preview validation; browser validation; coverage evidence.

Start services only through a documented local or disposable workflow. If execution is unsafe or blocked, record why and classify the blocker; do not invent a substitute that changes the intended workflow.

### 5. Check Operability and Enforcement

Compare documentation, executable scripts, observed behavior, and CI. Look for:

- commands whose failures or exit codes are masked;
- local checks that required CI does not enforce;
- CI jobs that configure a tool without exercising meaningful behavior;
- mutable, unpinned, or non-reproducible setup;
- stale paths, contradictions, or undocumented generated files;
- unclear ownership, component boundaries, change locations, or test placement;
- tests requiring undocumented services, fixtures, credentials, or cleanup;
- slow, noisy, flaky, or ambiguous feedback;
- missing artifacts or failure diagnostics;
- unsafe required operations or missing test-safe substitutes;
- missing branch, commit, review, ownership, or task-to-PR guidance.

Report strengths as well as gaps. Explicitly distinguish an **enforced control** from a documented intention.

### Cost Discipline

There is no fixed command budget, but an unanswered question is cheaper than an endless search. After roughly five attempts to resolve the same question, stop and record it as `not determined`, then score the affected area on the evidence you have. Never restart a completed phase.

## Probe

The command inventory proves only that commands exit 0. The probe proves the repository can guide a change to a *verified* fix. It is conditional.

**Run the probe when** the Gate 3 verification command executed in this environment — pass or fail — and the repository has code covered by it.

1. Prefer a genuine pre-existing failing check. Otherwise introduce one small, reversible defect inside the Gate 3 scope: invert a boolean, shift a boundary, drop a required field, change a public return value, violate a policy rule or fixture schema, or break a required document constraint.
2. Run the verification and confirm it catches the defect. **If nothing fails, that is a P0 or P1 fix record** — the path ships without a guard.
3. Fix and re-run until green.
4. Revert by rewriting the exact path you edited, then compare the full tree, tracked and untracked, against the baseline. The report is the only expected difference.

Record **locatability** (did the failure name file and line — quote it), **loop cost** (commands and wall-clock from edit to trustworthy green), **signal quality** (legible alone, or needed a debugger or outside knowledge), and **blockers** (what made a one-line change expensive).

**Do not run the probe when** the Gate 3 surface is repository-blocked or environment-blocked. Record `Probe: not attempted` with the blocking Fix Record IDs. Do not substitute an unrelated surface: proving that a documentation-mirror or metadata check detects drift says nothing about whether application changes are verifiable, and a substitute never satisfies Gate 4. If you run one anyway, label it `non-representative` and state plainly what it does not prove.

## Score Readiness

Score these areas across the full applicable scope. `Max` is the area's weight.

| # | Area | Max | Gate |
|---|---|---:|---|
| 1 | Agent guidance and navigation | 10 | |
| 2 | Reproducible environment and dependency setup | 10 | **Gate 1** |
| 3 | Build, package, render, or deliverable validation | 10 | **Gate 2** |
| 4 | Lint, format check, typecheck, static analysis, or policy validation | 10 | |
| 5 | Unit or component tests | 10 | |
| 6 | Integration, contract, or functional tests | 5 | |
| 7 | Runtime, API, CLI, or local-preview validation | 5 | |
| 8 | Browser or UI validation | 5 | |
| 9 | Coverage and feedback-loop quality | 5 | |
| 10 | CI enforcement and parity with local validation | 10 | |
| 11 | Safety, test isolation, artifacts, and cleanup | 5 | |
| 12 | Delivery workflow from task through review or PR | 5 | |
| 13 | Agent guardrails and permission scoping | 10 | |
| 14 | Context economy | 5 | |

Applicable maximum is 105 when every area applies.

Readiness status and points:

- **Verified:** full area points — executed successfully across the applicable scope, or proven by a currently required CI job.
- **Partial:** half the area points, rounded down — useful but incomplete, verified for only part of the scope, obtained through the unfrozen fallback, or documented but not fully proven.
- **Repository-blocked:** 0 — a repository-owned gap prevents reliable agent work.
- **N/A:** excluded from the applicable maximum; explain why.

Verification state: **Executed**, **Executed (unfrozen fallback)**, **CI-proven**, **Environment-blocked**, **Not run: unsafe**, or **Not applicable**.

An environment blocker is a confidence limitation, not an automatic zero, and never full credit: award at most half the area points, and only when repository evidence is coherent. Score the *property*, not a named command — there is no universal setup command. Award area 2 for pinned resolution in the ecosystem's own idiom, declared toolchain versions, documented external prerequisites, and an executed clean-checkout path; state whether setup was tested clean or only in a warmed workspace.

### Area 13 — Agent Guardrails

Score by capability rather than status. These are not interchangeable: instrumentation that reports an unsafe action afterward is not a control that prevents it. Named mechanisms are examples; credit any runtime's equivalent, including mechanisms outside the agent runtime.

| Capability | Pts | Earns credit |
|---|---:|---|
| Prevention | 4 | Blocks an unsafe action before it happens: a pre-tool gate denying reads or writes to secret paths, a scoped allow-list, protected paths, approval before an outward-facing write. |
| Observation | 2 | Records what the agent did: post-edit hooks, audit logs, artifact capture, secret redaction. |
| Completion | 2 | A tracked run-finished signal, so lifecycle state cannot go stale. |
| Enforcement | 2 | Controls outside the agent's cooperation: CI that actually runs the verification suite, pre-commit with a deterministic install path, a non-privileged runtime user, resource limits, restricted egress, branch protection. |

**Negative controls cap area 13 at 2 regardless of what else exists**, and each is its own P0 or P1 fix record: a permission bypass in any committed script, task runner, container definition, or CI job; a blanket allow-all policy; a readable secret file with no guard; a plaintext credential in the repository or shipped configuration. Report the path, never the value.

A rule that lives only in prose is described, not enforced; it scores under area 1.

### Area 14 — Context Economy

Score the cost of reading this repository well enough to change it: oversized files on the paths an agent must actually open, duplicated or contradictory instruction sources, stale instructions that contradict the code, and undocumented generated files an agent may waste effort editing.

Measure, but tie every measurement to observed friction. Counting files over roughly 800 lines is evidence only when one of them sits on the change path you traced, or on the path a Fix Record requires editing. Exclude vendored, generated, and resolution files. A raw size statistic with no friction attached is not a finding.

### Gates

Each gate is anchored to a scored area. A gate's result **is** its anchor area's score; never report a separate gate number.

| Gate | Anchor |
|---|---|
| Gate 1 — setup | Area 2 |
| Gate 2 — deliverable | Area 3 |
| Gate 3 — primary verification | The area holding the archetype's primary verification surface, named explicitly: usually area 5, area 6 where functional tests are the real coverage, or area 4 for documentation and infrastructure archetypes |
| Gate 4 — probe | The probe result, or `not attempted` with its blocking Fix Record IDs |

Gates 1 to 3 pass only when the anchor area is **Verified** at full points. State which area anchors Gate 3 and why.

Gate 4 passes when the probe's verification detected the defect and the loop returned to green. It fails when the probe ran and nothing detected the defect. When Gate 3 was blocked, Gate 4 is `not attempted`: it neither passes nor fails, and it caps confidence rather than forcing a status.

### Score and Status

`normalized score = round(points earned / applicable maximum * 100)`

Report the raw total, the applicable maximum, every N/A subtraction, and the addends on one line so a reviewer can re-add them without re-reading the repository.

Verification confidence:

- **High:** Full scope audited; at least 80% of applicable executable areas, including every gate, are executed or CI-proven; the probe completed when required.
- **Medium:** Full scope audited; 50–79% are executed or CI-proven, or one gate is environment-blocked with coherent repository evidence.
- **Low:** Less than 50% are proven, multiple gates are unproven, a required probe did not complete, or important scope is unaudited.

Overall status:

- **Ready:** Every gate passes, the probe passed when required, score is at least 80, confidence is High or Medium, no P0 repository blocker remains, and no negative control was found.
- **Partially ready:** Score 50–79; or score at least 80 with a gate that fails only for environment reasons, Low confidence, or another material validation gap.
- **Not ready:** Score below 50, any gate's anchor area is Repository-blocked, the probe ran and nothing detected the defect, or an agent cannot reliably understand, set up, change, or validate the repository.

Never let a high average hide a failed gate. Treat the score as a comparison and trend signal; use evidence, gates, and fixes for decisions.

## Create Fix Records

Create one stable record per problem: `F-01`, `F-02`, and so on. Findings and actions are one object, so they cannot drift apart. Include:

- **Problem:** One concrete sentence.
- **Blocks:** The specific agent capability lost — "blocks producing the frontend deliverable", not "hurts maintainability".
- **Evidence:** A `path:line`, executed command with its result, or quoted failure. For a non-`repo` owner, cite the command you ran in this environment and what it returned.
- **Priority:** P0, P1, or P2.
- **Owner:** `repo`, `agent-environment`, `platform`, or `external-service`. Choose the narrowest that actually fixes it.
- **Target:** The file, control, or generic external artifact that changes. Mark unverifiable external targets as unverified.
- **Fix:** An imperative action. If unknown, name the investigation required and mark it `needs-investigation`.
- **Verify:** A command or objectively observable result that closes the record. Never prose that a reader cannot run or check.
- **Level:** `code`, `control`, `docs`, or `instructions`.

Priorities:

- **P0:** Unattended work stops and needs a human.
- **P1:** The agent can proceed incorrectly or without meaningful validation.
- **P2:** The agent succeeds with avoidable cost, ambiguity, or weak feedback.

Every failed gate and every negative control has a record. Prefer `code`, then an executable `control`, before `docs` or `instructions`. Documentation is not a sufficient fix for a broken command or missing enforcement.

Order records by priority, then by expected effort when reasonably known, so the cheapest high-priority wins come first. Keep environment and platform fixes separate from the repository improvement backlog.

## Output Quality Rules

- Give every line a consumer and a decision or action it enables. There are two consumers: the maintainer deciding what to repair and delegate, and the agent consuming structured state to plan or re-run.
- State each problem authoritatively in its Fix Record. Elsewhere cite its ID — but a table an FDE acts on must still carry complete wording. **Never write a bare `See F-01` in a cell whose purpose is to tell someone what to do.**
- Every scorecard cell cites a command row or a `path:line`.
- Do not add consistently empty columns or write `not measured` repeatedly. Include duration only when measured.
- Do not narrate compliance with this prompt. Avoid decorative metadata and hedged filler.
- Do not create a finding without a fix, or a fix without a finding.
- State each fact where the report assigns it and do not restate it elsewhere. The score, status, and confidence belong in the run block; the verdict paragraph interprets them in prose without repeating the commit or prompt version.
- No table exceeds seven columns; one line per cell; escape literal pipes as `\|`.
- Write the provisional report in one file-editing operation. Never assemble it with shell heredocs. The finalization exception in Final Validation permits the bounded rewrites needed to validate and truthfully record that command.

## Report

Write `reports/agentic-readiness.md` with an `# Agentic Readiness — <repository>` title, then these thirteen `##` sections in this order. Sections 1 to 8 are the decision document, ordered so a reader gets the whole readiness picture before the action list: verdict, then scope, then the scorecard, then what it means and what to do about it. Sections 9 to 13 are the supporting evidence.

### 1. Verdict

One short paragraph: the score, overall status, confidence, a one-sentence readiness conclusion, and the most expensive repository blocker named by ID. No commit, no prompt version, no table.

### 2. Run and Scope

A single fenced yaml block with exactly these top-level keys, in this order: `audited_by`, `prompt_version`, `started`, `completed`, `commit`, `branch`, `platform`, `archetype`, `scope`, `baseline_worktree`, `final_worktree`, `clean_state_setup` (verified, unfrozen fallback, warmed-workspace-only, or blocked with reason), `normalized_score`, `raw_total`, `applicable_maximum`, `status`, `confidence`, and a `gates` map. Follow `references/report-contract.md` for the machine-checked values and gate shape.

Then list components, workspaces, and explicit constraints, including the five host-execution fields from `references/agent-execution-contract.md` or `unavailable` with their `agent-environment` limitation.

### 3. Glossary

Reproduce the table below verbatim. It is fixed boilerplate: do not add terms, reword definitions, or expand it with repository-specific detail. Immediately below the table, add exactly one sentence in this format: `Gate 3 anchor: Area <4, 5, or 6> — <why this is the primary verification surface>.` Add no other content to this section.

| Term | Meaning |
|---|---|
| Area | One of 14 scored readiness dimensions. Each has a weight shown as `Max`. |
| Gate | One of 4 mandatory checks. A gate's result **is** its anchor area's score, not a separate number. Gates 1–3 pass only at full points. |
| Probe | Gate 4. A deliberate small defect introduced and reverted, to test whether the repository's own verification catches a real break. |
| `F-nn` | A Fix Record: one stable ID per problem, holding the finding and its fix together. |
| Priority | P0 stops unattended work and needs a human. P1 lets the agent proceed incorrectly or unvalidated. P2 costs avoidable time or clarity. |
| Owner | Who fixes it: `repo`, `agent-environment` (the agent's image or toolchain), `platform` (org or infra config), or `external-service`. |
| Readiness status | Per area: Verified (full points), Partial (half, rounded down), Repository-blocked (0), or N/A (excluded from the maximum). |
| Verification state | How the evidence was obtained: Executed, Executed (unfrozen fallback), CI-proven, Environment-blocked, Not run: unsafe, or Not applicable. |
| Level | What a fix changes: `code`, `control`, `docs`, or `instructions`. |
| Normalized score | `points earned / applicable maximum * 100`. The applicable maximum is 105 minus the weight of every N/A area, so it is rarely 100. |
| Repository blocker | The repository itself is missing, wrong, unsafe, or contradictory. Counts against readiness. |
| Environment blocker | The repository documents enough, but this audit machine lacked a tool, service, or permission. Caps confidence; never a full zero. |
| Enforced control | Something that actually fails when violated. A rule that lives only in prose is documented guidance, not an enforced control. |
| Negative control | A safety defect such as a permission bypass, allow-all policy, unguarded secret file, or committed plaintext credential. Caps area 13 at 2. |
| Unfrozen fallback | The locked install failed, so a non-mutating unlocked install was used instead. Valid evidence, but caps the setup area at half. |

### 4. Readiness Scorecard

Use:

`Area | Applicability | Status | Score | Verification | Evidence / Result | Fix IDs`

Include all fourteen areas, then the area 13 capability breakdown and any negative controls found. Follow `references/report-contract.md` for the machine-checked score and negative-control notation. Close with the raw total, applicable maximum, every N/A subtraction, the addends on one line, and the normalized score. Gate results belong in the next section; confidence belongs in sections 1 and 13.

The `Fix IDs` column lists IDs only. Do not restate problems here.

### 5. Mandatory Gates

Show each gate, its anchor area, its score, verification state, and blocking Fix Record IDs. Include the probe result or the reason it was not attempted.

### 6. What to Fix

Open with a compact index table, repository-owned fixes first, then environment or platform fixes:

`ID | Priority / Owner | Problem and blocked capability | Fix and target | Verify`

Every cell must be actionable on its own. Follow `references/report-contract.md` for the compact index. Each `F-nn` ID appears exactly once in the index and has exactly one matching record. Then give the authoritative full record for every `F-nn` ID, in ID order, with all nine fields. Start each record with `### F-nn`, then put each field on its own line as `**Problem:**`, `**Blocks:**`, `**Evidence:**`, `**Priority:**`, `**Owner:**`, `**Target:**`, `**Fix:**`, `**Verify:**`, and `**Level:**`. The index exists for triage and the records exist for execution; keep both, and keep their wording consistent.

### 7. What Can Be Delegated Today

Rate the work an AI coding agent can independently undertake today — research, implementation, testing, deliverable validation, runtime or API validation, browser validation, and autonomous task-to-PR delivery — as Yes, Partially, No, or N/A, each with the gate or Fix Record IDs behind it. Rate autonomous delivery **Yes** only when every gate passes, the probe succeeded, and area 13 scored prevention points above zero.

### 8. What Is Already Good

Give three to five evidence-backed strengths. Mark each as an enforced control or documented guidance, so nobody removes something load-bearing. If there are none, write `No strengths identified.` and say why.

### 9. Surface Resolution

Resolve each role and gate to an exact command with `Role | Resolved command | Source | Status | Justification`, including substitutes attempted and what they do not prove. The scorecard and gates cite these commands, so every command named in a scorecard cell must appear here.

### 10. Golden Path

Describe the clean-checkout workflow from setup through review or PR, and include the representative feature trace.

### 11. Probe

What was broken and where, how it was detected, locatability, loop cost, signal quality, blockers, and the baseline comparison result. If the probe was not attempted, state the blocking IDs and stop. If a non-representative substitute was used, say what it does not prove.

### 12. Commands Executed

List only meaningful commands actually executed, plus commands refused as unsafe with their class:

`Command | Directory | Source / Safety Class | Purpose | Result | Notes / Artifacts`

Add a duration column only when durations were measured consistently. Exclude attempts that failed because of your own tooling.

### 13. Confidence and Limits

Explain the confidence rating, important environment blockers, and any unaudited scope in no more than three short paragraphs. Then list every command or scope that could not be verified, its safety or blocker classification, and which conclusion it leaves uncertain. Nothing else.

## Final Validation

Re-read the report and verify:

- all thirteen sections exist in order, and every table is well formed and within seven columns;
- the glossary matches the prompt's table verbatim and names the Gate 3 anchor;
- each gate result equals its anchor area's score;
- the scorecard addends sum to the stated raw total, and the normalized score follows from it;
- every Fix Record has all nine fields, and every `Verify` is runnable or objectively observable;
- every ID in the index table has a full record, and their shared fields agree;
- no cell that requires action contains only a cross-reference;
- the probe section reports either a completed probe or an explicit reason it was not attempted;
- the report contains only commands actually executed or explicitly refused as unsafe;
- the final worktree differs from the baseline only by the report and known audit-created ignored artifacts, with the probe edit reverted.
- `python3 <skill-directory>/scripts/validate_report.py reports/agentic-readiness.md` exits 0;
- any unavailable host-execution control is recorded in Run and Scope constraints and Confidence and Limits as an `agent-environment` limitation.

Finalization exception: write the provisional report, run the validator, and make one corrective rewrite only if it fails. Run the validator once more after that correction. Then make one finalization rewrite that changes only Commands Executed and Confidence and Limits to record the last validator command and result. The finalization rewrite is permitted even when the provisional report passed; no other rewrite is allowed. Record unresolved validator errors in Confidence and Limits; say that you rewrote it, then stop.

Then respond with the report path, score, overall status, confidence, failed gates, the probe result, and the first repository-owned fix.
