---
name: architecture-audit
description: Systematic architecture review workflow. Use before major feature work on an unfamiliar or inherited codebase, before scaling milestones, or as a periodic health check. Maps the system as-built (not as-documented), dispatches parallel specialist reviews, and produces an evidence-backed findings report with severity verdicts.
---

# Architecture Audit

## The Law

```
AN ARCHITECTURE CLAIM WITHOUT A FILE REFERENCE IS AN OPINION.
"The service layer is tightly coupled" is not a finding.
"OrderService imports 14 concrete classes from 6 modules (src/services/order.ts:1-22),
so a payment-provider swap requires touching all 6" is a finding.
```

## When to Use

- Before major feature work on an inherited or unfamiliar codebase
- Before a scaling milestone (10× users, new region, new platform)
- After rapid growth phases where structure was sacrificed for speed
- As a periodic health check on long-lived systems
- NOT for greenfield design — use the **architect** agent and **brainstorming** skill instead

## Audit Workflow

### Step 1: Map the System As-Built

Document what the code actually does, not what the docs or diagrams claim. Read entry points, build files, and dependency manifests before any source.

```markdown
## System Map — YYYY-MM-DD

**Entry points:** (servers, CLIs, cron jobs, queue consumers — with file paths)
**Modules/layers:** (as they exist in the folder structure, not the intended design)
**External dependencies:** (databases, queues, third-party APIs — where each is called from)
**Data flow:** (request → response path for the 2-3 most important operations)
**Trust boundaries:** (where unvalidated input enters, where auth is checked)
```

If the as-built map contradicts existing architecture docs, record every divergence — each one is a finding.

### Step 2: Identify Load-Bearing Decisions

List the architectural decisions the system depends on, whether or not anyone made them deliberately:

| Decision | Where visible | Deliberate or accidental? |
|----------|--------------|--------------------------|
| Monolith vs services | repo layout, deploy config | |
| Sync vs async processing | queue usage, HTTP call chains | |
| Data ownership | which modules write which tables | |
| Coupling direction | import graph between layers | |
| State management | session stores, caches, singletons | |

### Step 3: Dispatch Parallel Specialist Reviews

Use the **dispatching-parallel-agents** skill. Each specialist gets the Step 1 system map plus a scoped question:

| Agent | Scoped question |
|-------|----------------|
| **architect** | Do module boundaries and coupling direction support the next 12 months of planned work? |
| **security-reviewer** | Are trust boundaries enforced at every entry point in the system map? |
| **performance-profiler** | Which architectural choices (N+1 patterns, sync chains, missing caches) cap throughput? |
| **database-reviewer** | Does data ownership match module boundaries? Any schema shared by unrelated modules? |
| **infra-reviewer** | Does the deploy topology match the code topology? Any single points of failure? |

Skip a specialist only if their domain is absent (e.g., no database → no database-reviewer).

### Step 4: Consolidate Findings with Evidence

Every finding must carry a file reference and a consequence:

```markdown
## Finding N: <one-line statement>

**Evidence:** `path/to/file.ts:12-40` — <what the code shows>
**Consequence:** <what breaks, slows, or blocks because of this>
**Effort to fix:** S / M / L
**Risk if unfixed:** <concrete scenario, not "tech debt">
```

Findings without evidence are deleted, not softened.

### Step 5: Classify Severity

| Severity | Criteria | Action |
|----------|---------|--------|
| **CRITICAL** | Data loss, security boundary bypass, or scaling wall within one milestone | Block feature work until addressed |
| **HIGH** | Change amplification — routine features require touching 3+ modules | Schedule before next major feature |
| **MEDIUM** | Coupling or duplication that slows work but doesn't block it | Backlog with owner |
| **LOW** | Style-level structure issues | Note only |

### Step 6: Verdict and Report

```markdown
## Architecture Audit — YYYY-MM-DD

**Scope:** <what was audited>
**System map:** (Step 1 output)
**Findings:** N critical / N high / N medium / N low
**Verdict:** SOUND | SOUND-WITH-RISKS | INTERVENTION-REQUIRED

**Top 3 actions:** (ordered by risk-to-effort ratio)
```

| Verdict | Criteria |
|---------|---------|
| **SOUND** | No critical or high findings — proceed with planned work |
| **SOUND-WITH-RISKS** | High findings exist with agreed mitigation dates |
| **INTERVENTION-REQUIRED** | Any critical finding — architecture work precedes feature work |

Feed CRITICAL and HIGH findings into the **writing-plans** skill as remediation plans. Record accepted risks as ADRs via the **architect** agent so the next audit can check whether the risk materialised.

## Rationalization Red Flags

- "The architecture is fine, the team just needs to be careful" — change amplification is structural, not behavioural
- "We'll audit after this next feature ships" — the next feature is built on the unaudited structure
- "The diagram in the wiki shows clean layers" — audit the code, not the diagram
