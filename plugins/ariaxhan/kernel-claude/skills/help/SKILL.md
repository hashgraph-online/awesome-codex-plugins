---
name: help
description: "Show KERNEL help. The unified skill system, state operations, agents, current plugin status. Triggers: help, how, what, skills, commands."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="help">

<purpose>
Quick reference for KERNEL v9.8.1.
One primitive: skills (methodology, workflows, state transitions, validators,
operators). Agents, manifests, philosophy, and current plugin status.
</purpose>

<host_invocation>
Claude Code invokes skills as `/kernel:<name>`. Codex invokes them as
`$kernel:<name>`. Tables below use Claude Code syntax; Codex users replace the
leading slash with a dollar sign.
</host_invocation>

<on_start>
Before showing help, check the actual state of the plugin as loaded in your context:
1. Is the session-start hook output visible? (Look for "# KERNEL" at conversation start)
2. Which profile is active? (local, github, github-oss, github-production)
3. Are there active contracts or pending reviews in AgentDB?
4. Report what you see, don't just recite docs.

```bash
agentdb recall "<feature> <subsystem> <files/symbols> <error/outcome>" --global
```
</on_start>

<getting_started>
| What you want | What to type |
|---------------|--------------|
| Set up a new project | `/kernel:init` |
| Start working on anything | `/kernel:ingest` + describe task |
| Run autonomously overnight | `/kernel:forge` + describe goal |
| Explore approaches creatively | `/kernel:dream` + describe problem |
| Debug something broken | `/kernel:diagnose` + describe symptom |
| Save progress before stopping | `/kernel:handoff` |
</getting_started>

<skills_reference>
## Core Workflow (kind: workflow)

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `/kernel:ingest` | Guided entry, classify, scope, execute | Default for any task. Human confirms each phase. |
| `/kernel:forge` | Autonomous engine, heat/hammer/quench/anneal | Run overnight. Iterates until antifragile or reports why not. |
| `/kernel:dream` | Creative exploration, 3 perspectives + stress test | When you need competing approaches before committing. |
| `/kernel:diagnose` | Systematic debugging + refactor analysis | Bugs, regressions, or before refactoring. Diagnosis before prescription. |
| `/kernel:simplify` | Cut cyclomatic complexity with AST-aware budgets, regression diffs, and a project gate | Jungle code, god functions, after any AI-written branchy function. A number, not an opinion. |

## Quality & Review (kind: validator)

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `/kernel:validate` | Pre-commit gates, build, lint, test, security | Before every commit. Blocks on failure. |
| `/kernel:tearitapart` | Critical pre-implementation review | Before tier 2+ work. Verdict: PROCEED/REVISE/RETHINK. |
| `/kernel:review` | Code review for PRs or staged changes | Before merging. >80% confidence threshold. |

## Learning & Observability

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `/kernel:retrospective` | Cross-session learning synthesis | When 5+ learnings accumulated. Clusters, deduplicates, promotes patterns into project hooks/agents/skills. |
| `/kernel:metrics` | Observability dashboard | Check session stats, agent success rates, hook health, learning utilization. |

## State Operations (kind: state_transition) — json-first

| Skill | Emits | When to use |
|-------|-------|-------------|
| `/kernel:handoff` | `kernel.handoff/v1` json manifest | Ending a session. Pins provenance, decisions, phases, context policy + budget. |
| `/kernel:checkpoint` | `kernel.checkpoint/v1` json manifest | MID-task save: safe context reset without full handoff ceremony. |
| `/kernel:retrospective` | `kernel.retrospective-result/v1` mutation record | 5+ learnings accumulated; promotes via artifact ladder. |
| `/kernel:ingest` (resume) | `kernel.context-receipt/v1` | Resuming: validates the manifest, checks divergence, compiles bounded context. |

Manifest CLI: `orchestration/manifest/kernel-manifest` (validate | latest | divergence |
preflight | compile | resume | activate | deactivate). Context policies: sealed (hook-blocked
forbidden globs) | bounded (extra loads ledgered) | advisory. Details: docs/MIGRATION-8.md.

## Setup

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `/kernel:init` | Confirm Vaults, create missing data dirs and three safe helper links | Once per machine, or helper-link recovery. |
| `/kernel:help` | This help | When you need a reminder. |
</skills_reference>

<flow_examples>
Typical flows, skills chain together:

**New feature:**
  ingest → (dream if complex) → tearitapart → execute → validate → review → handoff

**Bug fix:**
  diagnose → ingest (with diagnosis) → validate → review

**Overnight autonomous:**
  forge (runs heat/hammer/quench/anneal loop, ships when antifragile)

**End of session:**
  retrospective (if learnings accumulated) → handoff

**Long task, context filling up:**
  checkpoint → /clear → ingest (auto-discovers the checkpoint, resumes bounded)
</flow_examples>

<tiers>
Tier by reversibility x silence x blast radius; file count is only a weak hint.

| Tier | Risk profile | Your Role | Skills involved |
|------|--------------|-----------|-------------------|
| 1 | easy to undo, loud if wrong | Execute directly | ingest → validate |
| 2 | persistent or moderately quiet | Orchestrate, spawn surgeon | ingest → tearitapart → validate → review |
| 3 | hard to undo, quiet, wide blast | Orchestrate, surgeon + adversary | ingest → tearitapart → validate → review |
</tiers>

<agents>
These are Claude Code agent definitions. Codex does not register the files as native
agents; KERNEL applies the role contracts to available Codex subagents.

| Agent | Role |
|-------|------|
| **Surgeon** | Minimal diff implementation. Only touches contract-listed files. |
| **Adversary** | QA, assumes broken, finds edge cases, proves with evidence. |
| **Reviewer** | Code review with APPROVE/REQUEST CHANGES/COMMENT verdict. |
| **Researcher** | Finds proven solutions and anti-patterns before coding. |
| **Scout** | Codebase reconnaissance, maps structure, detects tooling. |
| **Validator** | Pre-commit quality gate, build, types, lint, tests, security. |
| **Dreamer** | Multi-perspective debate, minimalist/maximalist/pragmatist. |
</agents>

<lifecycle>
Claude Code runs the full declared plugin lifecycle. Codex runs supported synchronous
events, including SessionStart and write guards, but skips asynchronous command hooks
and has no plugin SessionEnd event. In Codex, use `$kernel:handoff` explicitly when
durable end-of-session state is required.
</lifecycle>

<philosophy>
<principle id="research_first">Research anti-patterns before solutions. Most problems are already solved.</principle>
<principle id="tests_first">Define success before coding. Tests before implementation.</principle>
<principle id="agentdb">Recall task context before acting. Recall again as the task changes. Write at end.</principle>
<principle id="big5">Big 5: input validation, edge cases, error handling, duplication, complexity.</principle>
<principle id="builtin">Built-in beats library. Library beats custom. Prove you need complexity.</principle>
</philosophy>

<tips>
- **Be specific**: "Add rate limiting to /api/upload" > "make it more secure"
- **Use the right skill**: diagnose for bugs, dream for design, ingest for everything else
- **Check metrics**: `/kernel:metrics` shows if learnings are being used or ignored
- **Save deliberately**: `/kernel:checkpoint` mid-task or `/kernel:handoff` before a session boundary
- **Run retrospective**: After several sessions, synthesize what you've learned
</tips>

</skill>
