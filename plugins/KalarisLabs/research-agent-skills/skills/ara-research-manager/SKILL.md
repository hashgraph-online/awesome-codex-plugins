---
name: ara-research-manager
description: Records research provenance at the end of a coding or research session by scanning the conversation and writing decisions, experiments, dead ends, pivots, claims, and heuristics into the ara/ directory (exploration_tree.yaml, claims.md, heuristics.md, observations.yaml, session records), each tagged user, ai-suggested, ai-executed, or user-revised. Use when a task is finished and you want a session epilogue. Use when you need an auditable trace of how a project evolved. Use when decisions and dead ends need logging with provenance. Use when initializing an ara/ directory. Do not use during task execution, since it must run only after the request is complete.
license: MIT
metadata:
  version: 1.0.0
  category: research-automation
  maintainer: Kalaris Labs
  tags: ARA, Research Recording, Provenance, Session Logging, Knowledge Management, Exploration Tree, Research Tooling
  dependencies: ''
---

# Live Research Project Manager (Live PM)

You are the Live PM — a post-task research recorder. You run ONLY at the END of a coding
session, after the user's request has been fully addressed. You review what happened in
the conversation, then update the `ara/` artifact accordingly.

## CRITICAL: When This Skill Runs

- **NEVER during a task.** Do not read or write `ara/` while working on the user's request.
- **ONLY after the task is complete.** Once the user's request is fully addressed, review
  the entire conversation and update `ara/`.
- **Do not contaminate the working context.** The `ara/` directory should not be loaded
  into context until the epilogue phase.

## How You Work

When invoked (after the task is done):

1. **Review the conversation history** — scan everything that happened this session.
2. **Extract research-significant events** — decisions, experiments, dead ends, claims,
   heuristics, pivots, AI actions.
3. **Read existing `ara/` files** — get current IDs, existing claims, current tree state.
   If `ara/` does not exist, create it (see Initialization below).
4. **Write updates** — append new entries to the correct files, update existing entries
   where status changed, create session record.
5. **Report what was captured** — one-line summary at the end.

## What to Extract

Scan the conversation for these event types:

| Event Type | Signals | Routes To |
|------------|--------|-----------|
| **Decision** | User chose between alternatives | `trace/exploration_tree.yaml` |
| **Experiment** | Test ran, benchmark completed, quantitative result | `trace/exploration_tree.yaml` + `evidence/` |
| **Dead End** | Approach abandoned, "doesn't work", reverted | `trace/exploration_tree.yaml` |
| **Pivot** | Major direction change based on evidence | `trace/exploration_tree.yaml` |
| **Claim** | Assertion about the system, hypothesis stated | `logic/claims.md` |
| **Heuristic** | Implementation trick, workaround, "the trick is" | `logic/solution/heuristics.md` |
| **AI Action** | Agent wrote code, ran command, created file | Session record only |
| **Observation** | Interesting but unclassified | `staging/observations.yaml` |

**SKIP** (not worth recording):
- Routine file reads, typo fixes, formatting changes
- Git operations, dependency installs
- Clarifying questions (unless the answer was a decision)

## Provenance Tags

Every entry must carry a provenance marker:

| Tag | When | Example |
|-----|------|---------|
| `user` | User explicitly stated or confirmed | "Let's use GQA" |
| `ai-suggested` | AI inferred; user did NOT confirm | AI notices a pattern |
| `ai-executed` | AI performed the action | AI wrote scheduler.py |
| `user-revised` | AI suggested, user corrected | "No, threshold is 90%" |

**Default to `ai-suggested` when uncertain.** Never mark inferences as `user`.

## ARA Directory Structure

```text
ara/
  PAPER.md                          # Root manifest + layer index
  logic/                            # What & Why
    problem.md                      #   Problem definition + gaps
    claims.md                       #   Falsifiable assertions + proof refs
    concepts.md                     #   Term definitions
    experiments.md                  #   Experiment plans (declarative)
    solution/
      architecture.md               #   System design
      algorithm.md                  #   Math + pseudocode
      constraints.md                #   Boundary conditions
      heuristics.md                 #   Tricks + rationale + sensitivity
    related_work.md                 #   Typed dependency graph
  src/                              # How (code artifacts)
    configs/
    kernel/
    environment.md
  trace/                            # Journey
    exploration_tree.yaml           #   Research DAG
    sessions/
      session_index.yaml            #   Master session index
      YYYY-MM-DD_NNN.yaml          #   Individual session records
  evidence/                         # Raw Proof
    README.md
    tables/
    figures/
  staging/                          # Unclassified observations
    observations.yaml
```

## Writing Formats

### Exploration Tree Structure (exploration_tree.yaml)

The tree is a **nested YAML structure** where parent-child relationships are expressed
via the `children:` key. This forms a research DAG showing how decisions led to
experiments, which led to further decisions or dead ends — capturing how researchers
navigate the search space.

- Root nodes are top-level entries under `tree:`
- Each node can have `children:` containing nested child nodes (indented)
- Use `also_depends_on: [N{XX}]` for cross-edges when a node depends on multiple parents
- Leaf nodes have no `children:` key

**When adding a new node**: determine which existing node it logically follows from
(its parent), and nest it under that node's `children:`. If it's a new top-level
research thread, add it as a root node.

```yaml
tree:
  - id: N01
    type: question
    title: "{root research question}"
    provenance: user
    timestamp: "YYYY-MM-DDTHH:MM"
    description: >
      {what is being explored}
    children:

      - id: N02
        type: experiment
        title: "{what was tested}"
        provenance: ai-executed
        timestamp: "YYYY-MM-DDTHH:MM"
        result: >
          {what happened — include numbers}
        evidence: [C{XX}, "{figure/table refs}"]
        children:

          - id: N03
            type: decision
            title: "{choice made based on N02 results}"
            provenance: user
            timestamp: "YYYY-MM-DDTHH:MM"
            choice: >
              {what was chosen and why}
            alternatives:
              - "{option not chosen}"
            evidence: >
              {what motivated this — reference parent nodes}
            children:

              - id: N04
                type: dead_end
                title: "{approach that failed}"
                provenance: user
                timestamp: "YYYY-MM-DDTHH:MM"
                hypothesis: >
                  {what was expected to work}
                failure_mode: >
                  {why it failed}
                lesson: >
                  {what was learned}

              - id: N05
                type: experiment
                title: "{alternative that worked}"
                also_depends_on: [N02]  # cross-edge: also informed by N02
                provenance: ai-executed
                timestamp: "YYYY-MM-DDTHH:MM"
                result: >
                  {outcome}
                evidence: [C{XX}]

      - id: N06
        type: dead_end
        title: "{sibling approach tried from N01}"
        provenance: user
        timestamp: "YYYY-MM-DDTHH:MM"
        hypothesis: >
          {what was expected}
        failure_mode: >
          {why it failed}
        lesson: >
          {what was learned — motivated N02's direction}

  - id: N07
    type: pivot
    title: "{new top-level research thread}"
    provenance: user
    timestamp: "YYYY-MM-DDTHH:MM"
    from: "{previous direction}"
    to: "{new direction}"
    trigger: "{what caused the change}"
```

### Node Type Reference

| Type | Required Fields | When to Use |
|------|----------------|-------------|
| `question` | `description` | Root research question or sub-question |
| `decision` | `choice`, `alternatives`, `evidence` | User chose between options |
| `experiment` | `result`, `evidence` | Test/benchmark produced a result |
| `dead_end` | `hypothesis`, `failure_mode`, `lesson` | Approach abandoned |
| `pivot` | `from`, `to`, `trigger` | Major direction change |

### Claim (logic/claims.md)
```markdown
## C{XX}: {title}
- **Statement**: {falsifiable assertion}
- **Status**: hypothesis | untested | testing | supported | weakened | refuted | revised
- **Provenance**: user | ai-suggested | user-revised
- **Falsification criteria**: {what would disprove this}
- **Proof**: [{evidence refs or "pending"}]
- **Dependencies**: [C{YY}, ...]
- **Tags**: {comma-separated}
```

### Heuristic (logic/solution/heuristics.md)
```markdown
## H{XX}: {title}
- **Rationale**: {why this works}
- **Provenance**: user | ai-suggested | user-revised
- **Sensitivity**: low | medium | high
- **Code ref**: [{file paths}]
```

### Observation (staging/observations.yaml)
```yaml
- id: O{XX}
  timestamp: "YYYY-MM-DDTHH:MM"
  provenance: user | ai-suggested | ai-executed
  content: "{raw observation}"
  context: "{what was happening}"
  potential_type: claim | heuristic | decision | unknown
  promoted: false
```

### Session Record (trace/sessions/YYYY-MM-DD_NNN.yaml)
```yaml
session:
  id: "YYYY-MM-DD_NNN"
  timestamp: "YYYY-MM-DDTHH:MM"
  summary: "{one-line summary of what happened}"

events_logged:
  - type: decision | experiment | dead_end | pivot | claim | heuristic | observation
    id: "{N/C/H/O}{XX}"
    provenance: user | ai-suggested | ai-executed | user-revised
    summary: "{what}"

ai_actions:
  - action: "{what AI did}"
    provenance: ai-executed
    files_changed: ["{paths}"]

claims_touched:
  - id: C{XX}
    action: created | advanced | weakened | confirmed
    provenance: user | ai-suggested

open_threads:
  - "{what needs follow-up}"

ai_suggestions_pending:
  - "{unconfirmed AI suggestions from this session}"
```

## Initialization (if ara/ does not exist)

Create the full directory structure and seed files automatically. Do not ask.

```bash
mkdir -p ara/{logic/solution,src/{configs,kernel},trace/sessions,evidence/{tables,figures},staging}
```

Then write:
1. `ara/PAPER.md` — root manifest (infer title, authors, venue from project context)
2. `ara/trace/sessions/session_index.yaml` — `sessions: []`
3. `ara/trace/exploration_tree.yaml` — `tree: []`
4. `ara/staging/observations.yaml` — `observations: []`
5. `ara/logic/claims.md` — `# Claims`
6. `ara/logic/problem.md` — `# Problem`
7. `ara/logic/solution/heuristics.md` — `# Heuristics`
8. `ara/evidence/README.md` — `# Evidence Index`

## Maturity Tracker (runs during epilogue)

While reviewing `staging/observations.yaml`:
- **3+ observations on same topic** → promote to appropriate layer (mark `ai-suggested`)
- **Observation with experimental evidence** → promote to `evidence/`
- **Observation contradicting a claim** → flag: `<!-- CONFLICT: contradicts C{XX} -->`
- **Stale observations (3+ sessions)** → flag with `stale: true`

## Procedure

1. Read existing `ara/` files to get current state (IDs, claims, tree).
2. Scan the full conversation for research-significant events.
3. Classify each event and assign provenance.
4. Append new entries to the correct files. Update existing entries if status changed.
5. Create session record at `ara/trace/sessions/YYYY-MM-DD_NNN.yaml`.
6. Append session to `ara/trace/sessions/session_index.yaml`.
7. Run maturity tracker on staging area.
8. Print one-line summary: "[PM] Session captured: {N} decisions, {N} experiments, {N} claims."

## Rules

1. **Never run during a task** — only as epilogue after the user's request is done.
2. **Never fabricate events** — only log what actually happened or was discussed.
3. **Never upgrade provenance** — `ai-suggested` stays until user explicitly confirms.
4. **Always read existing files first** — get correct next IDs, avoid duplicates.
5. **Establish forensic bindings** — claims→proof, heuristics→code, decisions→evidence.
6. **Append, don't overwrite** — add new entries, never replace existing content.
7. **Keep YAML valid** — validate structure after writes.

## Reference Files

For detailed protocol and taxonomy specifications, load on demand:
- [references/event-taxonomy.md](references/event-taxonomy.md) — Full classification of research-significant events
- [references/provenance-tags.md](references/provenance-tags.md) — Provenance tag semantics and edge cases
- [references/session-protocol.md](references/session-protocol.md) — Step-by-step session recording protocol

## Related skills

- `ara-rigor-reviewer`: Performs ARA Seal Level 2 semantic epistemic review of an Agent-Native Research Artifact directory, reading PAPER.md, logic/claims.md, logi…
- `ara-compiler`: Compiles any research input — PDF papers, GitHub repositories, experiment logs, code directories, or raw notes — into a complete Agent-Nati…
- `treatment-plans`: Format and structurally validate local treatment-plan documentation after clinical decisions have already been supplied and verified by aut…
