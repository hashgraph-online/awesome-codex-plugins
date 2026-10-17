---
name: brownfield-adoption
description: >
  Step-by-step process for adopting Cavekit on an existing codebase.
  Covers the 6-step brownfield process, bootstrap prompt design, spec validation against
  existing behavior, and the decision between brownfield adoption vs deliberate rewrite.
  Trigger phrases: "brownfield", "existing codebase", "add Cavekit to existing project",
  "adopt Cavekit", "layer kits on code", "retrofit kits"
---

# Brownfield Adoption: Adding Cavekit to Existing Codebases

Brownfield adoption layers kits on top of existing code without rewriting it. The existing codebase becomes reference material, and kits are reverse-engineered from what the code actually does. Once kits exist, all future changes flow through the Cavekit lifecycle.

**Core principle:** The existing code is not the enemy -- it is the source of truth for cavekit generation. Respect what works; cavekit what matters.

---

## 1. When to Use Brownfield Adoption

Brownfield adoption is the right choice when:

- You have a **working codebase** that you want to improve incrementally
- You want to adopt Cavekit **without stopping development**
- The codebase is too large or critical for a full rewrite
- You want **traceability** between kits and code for future changes
- You need to **onboard AI agents** to an existing project safely
- The team wants to start with Cavekit on a subset of the codebase

**Brownfield is NOT the right choice when:**
- You are migrating to a completely different framework (use a deliberate rewrite instead)
- The existing code is so broken that kits would just document bugs
- The codebase is being sunset or replaced

---

## 2. Brownfield vs Deliberate Rewrite

Before starting, decide which approach fits your situation:

| Dimension | Incremental Adoption | Clean-Slate Rebuild |
|-----------|---------------------|---------------------|
| **Objective** | Add cavekit coverage around working code | Replace the codebase with a new implementation |
| **What happens to existing code** | Remains in place, evolves under Cavekit governance | Archived once kits are extracted; new code replaces it |
| **Risk profile** | Lower -- production system stays functional throughout | Higher -- new system must achieve feature parity before cutover |
| **Time to first value** | Fast -- kits appear in days, improvements follow | Slow -- significant upfront investment before any return |
| **Ideal scenarios** | Production systems, incremental improvement, large legacy codebases | Technology stack changes, irrecoverable tech debt, greenfield-quality rebuilds |
| **How kits originate** | Derived by analyzing existing behavior | Written forward from product requirements |
| **Handling broken behavior** | Kits capture current state; bugs are fixed through normal Cavekit cycles | Kits capture intended state; fresh implementation avoids old bugs |
| **Impact on ongoing work** | Low -- regular development continues alongside adoption | High -- team capacity is split between old and new systems |

### Decision flowchart

```
Is the existing code fundamentally sound?
  YES -> Are you changing frameworks?
           YES -> Deliberate Rewrite (extract specs, build new)
           NO  -> Brownfield Adoption (layer specs, evolve)
  NO  -> Is a rewrite feasible (time, budget, risk)?
           YES -> Deliberate Rewrite
           NO  -> Brownfield Adoption (spec the broken parts, fix incrementally)
```

---

## 3. The 6-Step Brownfield Process

### Step 1: Set Up the Context Directory

Create the standard Cavekit context directory structure alongside your existing codebase:

```bash
mkdir -p context/{refs,kits,plans,impl,prompts}
```

Resulting structure:

```
your-project/
+-- src/                    # Existing source code (untouched)
+-- tests/                  # Existing tests (untouched)
+-- package.json            # Existing config (untouched)
+-- context/
    +-- refs/
    |   +-- architecture-overview.md   # High-level description of existing system
    +-- kits/
    |   +-- CLAUDE.md                  # "Kits define WHAT needs implementing"
    +-- plans/
    |   +-- CLAUDE.md                  # "Plans define HOW to implement something"
    +-- impl/
    |   +-- CLAUDE.md                  # "Impls record implementation progress"
    +-- prompts/
        +-- 000-generate-kits-from-code.md   # Bootstrap prompt (this step)
```

**Create `context/refs/architecture-overview.md`** with a high-level description of the existing system:

```markdown
# Architecture Overview

## System Description
{Brief description of what the application does}

## Technology Stack
- Language: {LANGUAGE}
- Framework: {FRAMEWORK}
- Build: {BUILD_COMMAND}
- Test: {TEST_COMMAND}

## Directory Structure
{Key directories and their purposes}

## Key Domains
{List the major functional areas of the application}

## External Dependencies
{APIs, databases, services the application depends on}

## Known Issues / Tech Debt
{Major known issues that specs should account for}
```

### Step 2: Designate the Codebase as Reference Material

The existing codebase itself becomes the reference material. Unlike greenfield projects (where refs are PRDs or language specs), brownfield refs are the living code.

**In `context/refs/`, add a pointer:**

```markdown
# Reference: Existing Codebase

The existing source code at `src/` is the primary reference material for spec generation.

## How to Use This Reference
1. Explore the codebase structure to identify domains
2. Read source files to understand current behavior
3. Run existing tests to understand expected behavior
4. Check git history for context on design decisions

## What the Codebase Tells Us
- Current behavior (what the code DOES)
- Implicit requirements (what the code assumes)
- Test coverage (what is validated)
- Architecture decisions (how domains interact)

## What the Codebase Does NOT Tell Us
- Why decisions were made (check git history, docs)
- What behavior is intentional vs accidental
- What requirements are missing
- What the system SHOULD do vs what it DOES
```

### Step 3: Create the Bootstrap Prompt (000)

The bootstrap prompt is numbered `000` because it runs first and only once. It reverse-engineers kits from the existing code.

```markdown
# 000: Generate Kits from Existing Code (Brownfield Bootstrap)

## Runtime Inputs
- Framework: {FRAMEWORK}
- Build command: {BUILD_COMMAND}
- Test command: {TEST_COMMAND}
- Source directory: {SRC_DIR}

## Context
This is a brownfield adoption. The existing codebase at `{SRC_DIR}` is the reference material.
Read `context/refs/architecture-overview.md` for system context.

## Task

### Phase 1: Explore and Discover
1. Read the architecture overview
2. Explore the source directory structure
3. Identify distinct functional domains (auth, data, UI, API, etc.)
4. Read key source files in each domain
5. Run existing tests to understand expected behavior: `{TEST_COMMAND}`

### Phase 2: Generate Kits
For each identified domain:
1. Create `context/kits/cavekit-{domain}.md`
2. Each cavekit must include:
   - **Scope:** What this domain covers
   - **Requirements:** What the code currently does, expressed as requirements
   - **Acceptance Criteria:** Testable criteria derived from existing behavior
   - **Dependencies:** What other domains this depends on
   - **Out of Scope:** What this cavekit explicitly excludes
   - **Cross-References:** Links to related kits

3. Create `context/kits/cavekit-overview.md` as the index:
   - One-line summary per domain cavekit
   - Dependency graph between domains
   - Overall system architecture summary

### Phase 3: Validate
For each acceptance criterion in the generated kits:
1. Verify the existing code satisfies it
2. If a test exists that validates it, reference the test
3. If no test exists, note it as a coverage gap

## Exit Criteria
- [ ] All major domains have corresponding cavekit files
- [ ] Every requirement has testable acceptance criteria
- [ ] cavekit-overview.md indexes all kits
- [ ] Validation report shows which criteria are covered by existing tests
- [ ] Coverage gaps are documented

## Completion Signal
<all-tasks-complete>
```

### Step 4: Run the Iteration Loop

Run the bootstrap prompt through the iteration loop:

```bash
# Run 3-5 iterations to stabilize kits
iteration-loop context/prompts/000-generate-kits-from-code.md -n 5 -t 1h
```

**What happens during iteration:**
- **Iteration 1:** Agent explores codebase, generates initial kits (broad but shallow)
- **Iteration 2:** Agent refines kits based on git history from iteration 1, adds detail
- **Iteration 3:** Agent validates kits against code, fills coverage gaps
- **Iterations 4-5:** Convergence -- minor refinements, polishing cross-references

**Watch for convergence:** Kits should stabilize after 3-5 iterations. If they do not, the codebase may be too large for a single prompt. Split into domain-specific bootstrap prompts.

### Step 5: Validate Kits Match Behavior

After the bootstrap prompt converges, validate that the generated kits accurately describe the existing code:

#### 5a. Run tests against kits

```bash
# Use TDD to verify kits match behavior
# For each domain cavekit, generate tests from acceptance criteria
# then verify existing code passes them
{TEST_COMMAND}
```

#### 5b. Manual review checklist

```markdown
## Cavekit Validation Checklist
- [ ] Each domain in the codebase has a corresponding cavekit
- [ ] Acceptance criteria match actual code behavior (not aspirational)
- [ ] Dependencies between kits match actual code dependencies
- [ ] No orphan code -- every significant module is covered by a cavekit
- [ ] No phantom requirements -- kits do not describe behavior that does not exist
- [ ] Cross-references are accurate
```

#### 5c. Handle mismatches

| Mismatch Type | Action |
|--------------|--------|
| **Cavekit describes behavior that does not exist** | Remove the requirement (phantom requirement) |
| **Code has behavior not in any cavekit** | Add a requirement (coverage gap) |
| **Cavekit and code disagree on behavior** | Determine which is correct; update the other |
| **Code has bugs that kits documented as-is** | Mark as known issue in cavekit; fix via normal Cavekit |

### Step 6: Proceed with Normal Hunt

Once kits are validated, the project is ready for full Cavekit. All future changes flow through kits first:

```
Future change workflow:
  1. Update cavekit with new/changed requirement
  2. Generate/update plans from kits (prompt 002)
  3. Implement from plans (prompt 003)
  4. Validate: build + test + acceptance criteria
  5. If issues found: revise kits
```

Create the standard pipeline prompts:

```bash
# Create greenfield-style prompts for ongoing development
# (000 was the bootstrap; 001-003 are the ongoing pipeline)
context/prompts/001-generate-kits-from-refs.md    # For new features
context/prompts/002-generate-plans-from-kits.md   # Plan generation
context/prompts/003-generate-impl-from-plans.md    # Implementation
```

---

## 4. Incremental Adoption Strategy

You do not have to cavekit the entire codebase at once. Start with the most active or highest-risk areas:

### Priority matrix for cavekit coverage

| Priority | Criteria | Example |
|----------|----------|---------|
| **P0: Cavekit immediately** | Code changes frequently, high risk, many bugs | Auth system, payment processing |
| **P1: Cavekit soon** | Active development area, moderate complexity | Feature modules, API endpoints |
| **P2: Cavekit when touched** | Stable code, rarely changes | Utility libraries, config modules |
| **P3: Skip until needed** | Dead code, deprecated features | Legacy compatibility layers |

### Incremental process

```
Week 1: Bootstrap kits for P0 domains
  -> Run 000 prompt scoped to P0 directories only
  -> Validate and refine

Week 2-3: Extend to P1 domains
  -> Add P1 directories to the bootstrap prompt
  -> Cross-reference with existing P0 kits

Week 4+: Cavekit-on-touch
  -> When any P2 file is modified, generate its cavekit first
  -> Gradually expand coverage
```

### Scoping the bootstrap prompt

For incremental adoption, modify prompt 000 to target specific directories:

```markdown
## Scope
This bootstrap targets the following domains only:
- `src/auth/` -> cavekit-auth.md
- `src/payments/` -> cavekit-payments.md

Do NOT generate kits for other directories at this time.
```

---

## 5. Common Challenges and Solutions

### Challenge: Codebase is too large for one context window

**Solution:** Split the bootstrap into domain-specific prompts:

```
context/prompts/
+-- 000a-generate-kits-auth.md
+-- 000b-generate-kits-data.md
+-- 000c-generate-kits-ui.md
```

Run each independently, then create a manual `cavekit-overview.md` that ties them together.

### Challenge: No existing tests

**Solution:** The bootstrap prompt generates kits from code behavior, not tests. After kits exist, use the implementation prompt to generate tests:

```bash
# After bootstrap, generate tests from kits
iteration-loop context/prompts/003-generate-impl-from-plans.md -n 5 -t 1h
# Focus on test generation, not code changes
```

### Challenge: Code has undocumented behavior

**Solution:** Use git history to understand intent:

```markdown
# In the bootstrap prompt, add:

## Discovery Strategy
1. Read source code for current behavior
2. Read `git log --oneline -50` for recent changes
3. Read `git log --follow {file}` for individual file history
4. Infer requirements from both code AND history
```

### Challenge: Code has known bugs

**Solution:** Cavekit the intended behavior, not the buggy behavior. Mark known bugs as issues:

```markdown
### R3: Search Results Pagination
**Description:** Search results are paginated with 20 items per page
**Acceptance Criteria:**
- [ ] Results are paginated
- [ ] Page size is configurable (default 20)
**Known Issues:**
- BUG: Off-by-one error on last page (see issue #142)
```

### Challenge: Team resistance to Cavekit

**Solution:** Start small, show results:
1. Pick ONE upcoming feature
2. Write a cavekit before implementing it
3. Show how the cavekit caught issues the team would have missed
4. Gradually expand Cavekit coverage based on demonstrated value

---

## 6. Lightweight Cavekit for Small Projects

Even small projects benefit from minimal Cavekit. The "Cavekit floor" is:

```
your-small-project/
+-- src/
+-- context/
    +-- kits/
    |   +-- cavekit-task.md     # One cavekit for the current task
    +-- plans/
        +-- plan-task.md          # One plan for the current task
```

**No prompts directory needed.** Just write a focused cavekit and plan, then use the iteration loop against the plan.

**Why bother for small projects?**
- The cavekit catches requirements you would have missed
- The plan sequences work so the agent does not thrash
- If the project grows, you already have the structure in place
- It is much easier to scale up from lightweight Cavekit than to retrofit full Cavekit later

### Lightweight Cavekit process

1. Write `context/kits/cavekit-task.md` (15-30 minutes)
2. Write `context/plans/plan-task.md` (10-20 minutes)
3. Run the iteration loop against the plan
4. If the project grows, add the full context directory structure

---

## 7. Transition Milestones

Track your brownfield adoption progress with these milestones:

```markdown
## Brownfield Adoption Progress

### Milestone 1: Foundation
- [ ] Context directory created
- [ ] Architecture overview written
- [ ] Bootstrap prompt created

### Milestone 2: Initial Specs
- [ ] P0 domains have kits
- [ ] Kits validated against existing code
- [ ] Coverage gaps documented

### Milestone 3: Pipeline Active
- [ ] Standard prompts (001-003) created
- [ ] First feature developed through Cavekit pipeline
- [ ] Revision process tested

### Milestone 4: Steady State
- [ ] All active domains have kits
- [ ] All new features go through kits first
- [ ] Revision is routine
- [ ] Iteration loop runs are predictable (convergence in 3-5 iterations)

### Milestone 5: Full Cavekit
- [ ] All domains have kits
- [ ] All changes flow through the Hunt
- [ ] Convergence monitoring active
- [ ] Team comfortable with the process
```

---

## Cross-References

- **Context architecture:** See `ck:context-architecture` skill for the full context directory structure and progressive disclosure patterns.
- **Prompt pipeline:** See `ck:prompt-pipeline` skill for designing the 001-003 prompts after bootstrap.
- **Cavekit writing:** See `ck:cavekit-writing` skill for how to write high-quality kits with testable acceptance criteria.
- **Revision:** See `ck:revision` skill for tracing bugs back to kits after brownfield adoption.
- **Convergence monitoring:** See `ck:convergence-monitoring` skill for detecting when the bootstrap prompt has converged.
