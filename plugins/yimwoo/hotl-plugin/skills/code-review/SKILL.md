---
name: code-review
description: Use after completing implementation steps and before merging — reviews against plan and HOTL contracts.
---

# HOTL Code Review

User-facing entry point for getting a code review. Dispatches the full `code-reviewer` agent by default; falls back to inline review when subagents aren't available.

## Process

### 1. Gather Context

**Resolve base branch** (fallback ladder — use the first that succeeds):

1. PR base branch: `gh pr view --json baseRefName`
2. Repo default branch: `git symbolic-ref refs/remotes/origin/HEAD`
3. `main`
4. `master`

**Resolve review scope:**

- Feature branch: committed branch diff against base (`base...HEAD`), plus staged and unstaged local changes when present
- On base branch with staged changes: staged diff
- On base branch with unstaged changes: working tree diff
- On clean base branch: `HEAD~1..HEAD`
- Ambiguous (detached HEAD, no commits beyond base, no local changes): ask the user

**Detect workflow file:**

- First, glob for canonical workflows in `docs/plans/*-workflow.md`
- If one canonical match: use it
- If multiple canonical matches: prefer the most recently modified canonical workflow, unless the user named one
- If no canonical matches: glob for legacy `hotl-workflow-*.md` in project root
- If one legacy match: use it
- If multiple legacy matches: prefer the most recently modified legacy workflow, unless the user named one
- If no matches: proceed without workflow context

**Extract contracts** from workflow frontmatter if available (intent, constraints, success_criteria, risk_level).

**Gather verification evidence:**

- Primary (deterministic): `.hotl/state/*.json` and `.hotl/reports/*.md` — most recent artifacts if present
- Best-effort: recent test/lint output if discoverable; if unavailable, report "not available"

### 2. Dispatch Review

**If subagents are available (Claude Code, Codex):**

Dispatch the `code-reviewer` role as a subagent via the Agent tool. Use the structured dispatch template from `requesting-code-review`:

- Review type: `direct`
- Git range: resolved scope from step 1
- Workflow and contracts: if available
- Verification evidence: if available

**If subagents are not available (Cline, weaker runtimes):**

Run inline review in the current session using the same output contract. See "Inline Fallback" below.

### 3. Return Findings

- Present the review output (findings + verdict) to the user
- **Do NOT** automatically invoke `receiving-code-review`
- **Do NOT** automatically implement fixes
- If the user asks to fix the findings ("fix them", "address these", "implement the fixes"): then invoke `receiving-code-review`

## Verdict Model

Direct reviews use the final-review verdict model:

- **READY** — safe to merge
- **READY WITH WARNINGS** — safe to merge but warnings should be addressed soon
- **NOT READY** — blocking issues must be resolved before merge

## Review Lifecycle

```
code-review              = user-facing entry point for getting a review
requesting-code-review   = internal executor/orchestration entry point
receiving-code-review    = follow-up handler for acting on findings
```

## Output Contract

Both dispatched and inline reviews must conform to `docs/contracts/code-review-output.md`. Every review must contain these 6 sections in order: Scope (with verification evidence), Reviewed Dimensions, Findings, What Was Not Covered, Residual Risks, Verdict.

### Platform-Native Annotation Dedup

When the platform emits platform-native annotations for localized findings (e.g., `::code-comment` in Codex, inline GitHub review comments), do not restate those findings verbatim in the Findings section. Instead, use the grouped one-liner format defined in the output contract.

## Inline Fallback

When subagents are not available, run the review inline using the same output contract. The inline review must produce identical 6-section structure — not a weaker format.

### Dimensions

**Plan alignment** (when workflow provided):
- All steps in the workflow file completed
- success_criteria from frontmatter met
- No unplanned scope added (YAGNI)

When no workflow: state "Plan alignment: skipped (no workflow provided)"

**Code quality and design:**
- Tests exist and pass for all new behavior
- No code duplication introduced (DRY)
- Error handling at system boundaries only
- Reference `docs/checklists/architecture-and-design.md` for SOLID and architecture smell heuristics. If the checklist file is not available, continue with best-effort review.

**Security and reliability:**
- Reference `docs/checklists/security-and-reliability.md` for expanded security heuristics.
- Check for injection, auth gaps, race conditions, secret leakage, unsafe patterns.
- If the checklist file is not available, continue with best-effort review.

**Performance and boundary conditions:**
- Reference `docs/checklists/performance-and-boundary-conditions.md` for performance and boundary condition heuristics.
- Check for N+1 queries, unbounded memory, off-by-one, null handling, swallowed exceptions.
- If the checklist file is not available, continue with best-effort review.

**Removal and simplification:**
- Reference `docs/checklists/removal-and-simplification.md` for dead code and simplification heuristics.
- Flag unused exports, dead branches, feature-flagged-off code. Classify as safe-delete-now or defer-with-plan.
- If the checklist file is not available, continue with best-effort review.

**HOTL governance:**
- risk_level: high steps had human gate approval
- No sensitive data (secrets, PII) in code, logs, or comments
- Security-sensitive paths (auth, encryption) have human review documented

### Findings Format

Every finding must include:

```
- [SEVERITY]: file/path:line — description
  Why: [why this matters]
  Fix: [expected remediation direction]
```

For localized issues: file:line is required. For scope-level findings: provide the narrowest evidence available.

### Severity Levels

- **BLOCK:** Must fix before merge (failing tests, security issues, missing gates on high-risk steps)
- **WARN:** Should fix soon (code quality, missing docs for public APIs)
- **NOTE:** Consider in future (style, minor improvements)

BLOCK issues must be resolved before claiming done.

### Clean Review

Per the output contract, when a dimension has no findings it must still state what was checked, what was not covered, and residual risks. Additionally, the review must always include sections 4 (What Was Not Covered) and 5 (Residual Risks) even when no individual dimension has findings.
