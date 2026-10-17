---
name: context-architecture
description: |
  Progressive disclosure architecture for organizing project context as a DAG (directed acyclic graph).
  Agents enter at the root and traverse only the subgraph relevant to their task.
  Covers the 4-tier information flow (refs → kits → plans → impl), CLAUDE.md hierarchy
  across context/ and source tree, index files as DAG hub nodes, nesting rules, and backward compatibility.
  Trigger phrases: "context architecture", "progressive disclosure", "organize context for agents",
  "context directory structure", "how to structure docs for AI", "context hierarchy"
---

# Context Architecture: DAG-Based Progressive Disclosure

## Core Principle

**Agents should only read what they need.** Documents are organized as a directed acyclic graph (DAG) where index files act as hub nodes. An agent reads the index, identifies relevant edges, and follows only those to leaf documents. No agent ever loads the full tree.

---

## The 4-Tier Information Flow

```
refs/ (what IS)  -->  kits/ (what MUST BE)  -->  plans/ (HOW)  -->  impl/ (what WAS DONE)
     Tier 1                  Tier 2                     Tier 3              Tier 4
```

Each tier consumes the previous tier's output. Cross-references between tiers create the DAG edges that agents traverse.

---

## Directory Layout

```
context/
├── CLAUDE.md                              # Root entry node: describes all tiers + design layer
├── refs/                                  # Tier 1: Source material (read-only input)
│   ├── CLAUDE.md                          # "Source of truth. Organized by source. Read-only."
│   └── {source}/                          # Subdirs per source (e.g., prd/, api-spec/)
│       └── ...
├── kits/                            # Tier 2: WHAT to build
│   ├── CLAUDE.md                          # "Start at cavekit-overview.md. R-numbered reqs."
│   ├── cavekit-overview.md              # Index node (DAG hub)
│   ├── cavekit-{domain}.md              # Leaf — simple domain (single file)
│   └── {domain}/                          # Complex domain gets a subdirectory
│       ├── cavekit-{domain}.md          # Domain index (becomes hub node)
│       └── cavekit-{domain}-{sub}.md    # Sub-domain leaves
├── designs/                               # Cross-cutting: visual design system
│   ├── CLAUDE.md                          # "DESIGN.md at project root is canonical."
│   └── design-changelog.md               # Append-only change log
├── plans/                                 # Tier 3: HOW to build (task graphs)
│   ├── CLAUDE.md                          # "Start at plan-overview.md. Task dependency tiers."
│   ├── plan-overview.md                   # Index node
│   ├── build-site.md                      # Primary build site
│   ├── build-site-{feature}.md            # Feature-specific build sites
│   └── {domain}/                          # Complex plans get subdirectories
│       └── plan-{domain}-{area}.md
├── impl/                                  # Tier 4: What WAS DONE
│   ├── CLAUDE.md                          # "Start at impl-overview.md. Update after every session."
│   ├── impl-overview.md                   # Index node
│   ├── impl-{domain}.md                   # Per-domain tracking
│   ├── impl-review-findings.md            # Codex review findings ledger
│   ├── dead-ends.md                       # Failed approaches (shared across domains)
│   └── archive/                           # Compacted/archived tracking
```

> **Note:** `designs/` is a **cross-cutting constraint layer**, not a fifth tier. DESIGN.md (at project root) is read by agents at every Hunt phase — Draft reads it to constrain visual decisions, Architect references tokens in task descriptions, Build uses it for implementation, Inspect validates against it. It parallels how CLAUDE.md files provide conventions, but for visual design.

### Backward Compatibility: sites/ → plans/

Build sites previously lived in `context/sites/`. All Cavekit commands check both locations:

1. Look in `context/plans/`
2. If not found, fall back to `context/sites/`
3. If found in `sites/`, use it — no auto-migration, no breakage

`/ck:init` offers optional migration. Declining is permanent — the system works with either layout.

---

## CLAUDE.md Hierarchy

### Scope: Full Repository

`CLAUDE.md` files extend beyond `context/` into the source code tree. They form the connective tissue between code and the context DAG.

```
project/
├── CLAUDE.md                          # Project root: build/test commands,
│                                      #   "context/ has the full hierarchy"
├── context/
│   ├── CLAUDE.md                      # Root context node: 4 tiers described
│   ├── refs/CLAUDE.md                 # Tier 1 conventions
│   ├── kits/CLAUDE.md           # Tier 2 conventions
│   ├── plans/CLAUDE.md                # Tier 3 conventions
│   └── impl/CLAUDE.md                 # Tier 4 conventions
│
├── src/
│   ├── CLAUDE.md                      # Source code conventions
│   ├── auth/
│   │   ├── CLAUDE.md                  # "implements cavekit-auth.md R1-R3"
│   │   └── ...
│   └── parser/
│       ├── CLAUDE.md                  # "implements cavekit-grammar.md R1-R4,
│       │                              #   see plans/build-site.md T-012 through T-018"
│       └── ...
│
├── tests/
│   ├── CLAUDE.md                      # Test conventions, how to run
│   └── ...
└── scripts/
    ├── CLAUDE.md                      # Utility script conventions
    └── ...
```

### Loading Behavior

When an agent works in `src/auth/`, it loads hierarchically:
1. `project/CLAUDE.md` — project-level conventions
2. `project/src/CLAUDE.md` — source code conventions
3. `project/src/auth/CLAUDE.md` — **"implements cavekit-auth.md R1-R3"**

The third file bridges to the context DAG. The agent knows which cavekit to load without loading the entire `context/kits/` directory.

### CLAUDE.md Design Principles

- **Minimal** — 3-10 lines for source-tree files. Never duplicate cavekit content.
- **Connective** — each one names the cavekit requirements and plan tasks it relates to.
- **Contextual** — includes module-specific conventions (error handling patterns, test fixture locations).
- **Honest** — `/ck:make` only writes mappings it is certain about (tasks it completed, files it created).

---

## Progressive Disclosure: The DAG Traversal

### How Agents Navigate

1. **Enter at root** — read `context/CLAUDE.md` to understand the 4 tiers
2. **Select tier** — based on current task, navigate to the relevant tier's `CLAUDE.md`
3. **Read index** — the tier's overview file is the DAG hub, listing all domains with one-line summaries
4. **Follow edges** — read only the domain files relevant to the current task
5. **Cross-reference** — if a domain references another, follow that edge only if needed
6. **Nest deeper** — if a domain has subdirectories, its root file is the sub-index; spider from there

### Index File Format

Every overview file follows the same format:

```markdown
# Cavekit Overview

| Domain | File | Summary | Status |
|--------|------|---------|--------|
| Authentication | cavekit-auth.md | Registration, login, sessions, OAuth | DRAFT |
| Data Models | cavekit-data-models.md | Core entities, relationships, validation | DRAFT |
| Type System | cavekit-type-system.md | Effects lattice, tagged values (see type-system/) | DRAFT |
```

An agent reads this table, identifies "I need Authentication," and loads only `cavekit-auth.md`.

### Cross-Reference Edges

```markdown
**Dependencies:** cavekit-auth.md R2 (session tokens required for API auth)
**See also:** cavekit-api.md R4 (rate limiting uses auth identity)
```

Agents follow these only when the cross-referenced content is needed for the current task.

---

## Nesting Rule

A domain stays flat (single file) by default. When a file covers multiple independent concerns that could be understood separately, it becomes an index file pointing to a subdirectory.

**Trigger:** Cohesion, not line count. If a file has sections that an agent working on one section would never need to read the others, decompose it.

**Example:** `cavekit-type-system.md` covers effects lattice, tagged values, and inference rules:

```
kits/
├── cavekit-type-system.md                        # Now an index
└── type-system/
    ├── cavekit-type-system-effects.md
    ├── cavekit-type-system-tagged.md
    └── cavekit-type-system-inference.md
```

The original file stays in place as the index — no reference breakage.

---

## Backpropagation via CLAUDE.md

When a bug is found, source-tree CLAUDE.md files provide the reverse traversal:

```
Bug in src/auth/login.ts
    |
    v
src/auth/CLAUDE.md says "implements cavekit-auth.md R2"
    |
    v
cavekit-auth.md R2 — check acceptance criteria
    |
    |-- Criteria missing?  --> update cavekit (spec gap)
    |-- Criteria wrong?    --> fix cavekit (spec bug)
    |-- Criteria present but code violates? --> fix code (impl bug)
    |
    v
If cavekit changed --> propagate to plans/ --> flag affected tasks
```

### Forward Propagation

When a cavekit changes via `/ck:revise`:
1. Scan all `src/*/CLAUDE.md` files for references to the changed requirement
2. Flag those modules as potentially affected
3. New requirements with no source-tree CLAUDE.md references are unimplemented

---

## Bootstrapping

Run `/ck:init` to create the full hierarchy. It:
1. Scans existing project structure
2. Creates context directories (refs/, kits/, plans/, impl/)
3. Creates CLAUDE.md files using standard templates
4. Creates empty index files (cavekit-overview.md, plan-overview.md, impl-overview.md)
5. Offers migration if legacy `context/sites/` exists

Properties: idempotent, non-destructive, no questions asked.

---

## Build-Time Updates

After `/ck:make` completes, source-tree CLAUDE.md files are generated/updated:
- New source directories get a CLAUDE.md with cavekit/plan references
- Existing CLAUDE.md files get new references appended (never removed)
- `impl-overview.md` and `plan-overview.md` are updated with current status

---

## Multi-Repo Strategy

For shared kits across implementations, use git submodules:

```
Tier 1-2 (shared): shared-context/ (submodule)
    └── refs/ + kits/

Tier 3-4 (per-repo): context/
    └── plans/ + impl/
```

Each framework repo includes the shared context as a submodule. Updates propagate via `git submodule update`.

---

## Integration with Other Skills

| Skill | Integration |
|-------|------------|
| `ck:cavekit-writing` | Kits go in `context/kits/` following naming conventions |
| `ck:design-system` | DESIGN.md lives at project root; `context/designs/` has CLAUDE.md and changelog |
| `ck:impl-tracking` | Tracking lives in `context/impl/`, compacted when exceeding ~500 lines |
| `ck:validation-first` | Validation results recorded in impl tracking within the hierarchy |
| `ck:revision` | `/ck:revise` traverses CLAUDE.md edges in reverse to trace bugs to specs |
| `ck:methodology` | Context structure established during Draft phase, maintained throughout the Hunt |

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| Flat file dump | No progressive disclosure, agents load everything | Use standard directory structure with indexes |
| Missing CLAUDE.md files | No convention guidance, no DAG edges | Run `/ck:init` or add manually |
| Monolithic documents | Defeats progressive disclosure | Decompose into domains with overview indexes |
| Stale archives in active dirs | Wastes context window | Move to `impl/archive/` |
| Duplicating cavekit content in CLAUDE.md | Content drifts, double maintenance | CLAUDE.md files only contain references |
