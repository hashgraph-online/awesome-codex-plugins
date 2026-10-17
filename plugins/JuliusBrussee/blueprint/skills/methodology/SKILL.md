---
name: methodology
description: |
  Core Cavekit methodology — the master skill that teaches the Hunt lifecycle
  and routes to all sub-skills. Covers the Specify Before Building principle, the scientific method analogy,
  the four-phase Hunt lifecycle, decision matrix for when to use Cavekit, and build pipeline analogy.
  Trigger phrases: "use Cavekit", "cavekit methodology", "start Cavekit project", "cavekit methodology",
  "how should I structure this project for AI agents"
---

# Cavekit Methodology

## Core Principle: Specify Before Building

**Always define what you want before telling agents how to build it. Go through a cavekit stage — never jump straight from raw requirements to implementation.**

Cavekit is a methodology for building software with AI coding agents that **puts kits at the center of the development process — code is derived from them, not the other way around**. Whether starting from scratch or modernizing an existing system, the principle is the same:

- **Greenfield projects:** reference material → kits → code
- **Rewrites:** old code → kits → new code

In both cases, the kits become a living contract that agents consume to continuously build, validate, and refine the application.

### Why Kits Are the First-Class Citizen

| Property | Benefit |
|----------|---------|
| **Structured** | Organized as a navigable tree, enabling agents to load only what they need |
| **Human-legible** | Engineers can audit requirements at a higher level than code |
| **Stack-independent** | Decoupled from any single framework or language |
| **Independently evolvable** | Kits can be refined without touching implementation |
| **Verifiable** | Every requirement includes acceptance criteria agents can check |

> **Key Insight:** Well-written kits with strong validation make your application reproducible — any agent can rebuild it from the kits alone. Think of it as continuous regeneration.

---

## The Scientific Method Analogy

LLMs are inherently non-deterministic — like running an experiment, each individual call may yield different results. But through the right methodology — clear hypotheses, controlled conditions, and repeated trials — we extract reliable, reproducible outcomes from a stochastic process.

**Cavekit applies the scientific method to software construction — hypothesize, test, observe, refine.**

| Layer | Analogy | What It Does |
|-------|---------|-------------|
| **LLM calls** | Individual experiments | Each run may produce different results; no single output is authoritative |
| **Kits** | Hypotheses | Define what you expect to observe — the predicted behavior |
| **Validation gates** | Controlled conditions | Ensure reproducibility by constraining what counts as a valid outcome |
| **Convergence loops** | Repeated trials | Build statistical confidence through successive passes |
| **Implementation tracking** | Lab notebook | Record what was tried, what worked, and what failed |
| **Revision** | Revising the hypothesis | When results contradict expectations, update the theory upstream |

The outcome: a disciplined, repeatable engineering process layered on top of probabilistic generation.

---

## The 5 Hunt Phases

The Hunt is the four-phase lifecycle: **Sketch, Map, Make, Check**. Each phase has dedicated prompts that drive it.

| Phase | Input | Output | AI Role | Human Role |
|-------|-------|--------|---------|------------|
| **Draft** | Source materials, domain knowledge, existing systems | Implementation-agnostic kits | Extract requirements, structure knowledge | Verify kits capture intent accurately |
| **Architect** | Kits + framework research | Framework-specific implementation plans | Design architecture, break down work, order steps | Approve architectural choices |
| **Build** | Plans + kits | Working code + tests + tracking docs | Write code, run tests, check against kits | Watch for drift and blockers |
| **Inspect** | Failed validations, gaps, manual fixes | Updated kits/plans via revision | Identify root causes, propagate fixes upstream | Evaluate outcomes, set priorities |
| **Monitor** | Running application, git history | Issues, anomalies, progress reports | Scan for regressions, surface metrics | Interpret reports, guide next steps |

### Phase Transitions

Each phase has **gate conditions** that must be met before moving to the next:

1. **Draft → Architect:** All domains have kits with testable acceptance criteria. Human has reviewed for completeness.
2. **Architect → Build:** Plans reference kits, define implementation sequence, and include test strategies. Architecture decisions validated.
3. **Build → Inspect:** Code builds, tests pass at current coverage level, implementation tracking is up to date.
4. **Inspect → Monitor:** Convergence detected (changes decreasing iteration-over-iteration). Remaining changes are trivial.
5. **Monitor → Draft (cycle):** Gap found or new requirement identified. Revise kits and restart the cycle.

The **Inspect** phase is where the human serves as **reviewer and decision-maker**, not hands-on coder. You monitor the process, request changes as needed, and make systemic improvements to kits and prompts.

> For the full Hunt phase reference, see `references/hunt-phases.md`.

---

## Decision Matrix: When to Use Cavekit

### Full Cavekit

Use when the project has significant scope, evolving requirements, or needs autonomous agent execution.

| Indicator | Threshold |
|-----------|-----------|
| Codebase size | 50+ source files |
| Requirements | Evolving, multi-domain |
| Agent coordination | Multi-agent or multi-prompt pipelines |
| Environment | Production, security-sensitive, brownfield |
| Team structure | Multi-team or cross-team |
| Execution mode | Long-running autonomous work (overnight, unattended) |

**What you get:** Full Hunt lifecycle, context directory with kits/plans/impl tracking, prompt pipeline, convergence loops, revision, validation gates.

### Lightweight Cavekit

Use when scope is moderate — too complex for ad-hoc but not worth a full pipeline.

| Indicator | Threshold |
|-----------|-----------|
| Codebase size | 5-50 files |
| Requirements | Mostly clear, focused |
| Agent coordination | Single agent, possibly with sub-agents |
| Execution mode | Interactive with occasional iteration loops |

**What you do:**
1. Write a focused `context/kits/cavekit-task.md` capturing requirements
2. Add a `context/plans/plan-task.md` sequencing the implementation
3. Skip full Hunt — just run an iteration loop against the plan

This is the "Cavekit floor" — most of the benefit without the overhead of a full multi-phase pipeline.

### Skip Cavekit

Use when the task is trivially small.

| Indicator | Threshold |
|-----------|-----------|
| Codebase size | Less than 5 files |
| Task type | One-off tools, simple bug fixes, exploratory prototypes |
| Implementation | Fits comfortably in one agent session without needing external references |

**Heuristic:** If the whole task fits in one context window with room to spare, full Cavekit adds more overhead than value.

### Growth Path

Start with lightweight Cavekit even if the project is small. If the scope expands, you already have the structure in place to scale up. It is much harder to retrofit kits onto a large codebase than to grow a cavekit directory from the beginning.

---

## The CI Pipeline Analogy

Cavekit mirrors a **build pipeline** — each stage transforms input into validated output, with feedback loops that propagate corrections upstream:

```
Traditional CI/CD:
  Code → Build → Test → Deploy

Cavekit AI Pipeline:
  Cavekit Change
    → Generate Plans (iteration loop)
    → Generate Implementation (iteration loop)
    → Validate (Tests + Review)
    → Human Audit (Monitor & Steer)
    → [Gap Found]
    → Revise
    → Cavekit Change (cycle repeats)
```

Every stage can run as an iteration loop — the same prompt executed repeatedly until output stabilizes. The iteration loop is what transforms nondeterministic LLM output into predictable, validated software.

### The Iteration Loop

The iteration loop is the fundamental execution unit in Cavekit. Execute the same prompt against the same codebase multiple times until the delta between runs approaches zero.

**Mechanics:**
1. Execute a prompt against the current codebase
2. The agent inspects git history and tracking documents to understand what has already been done
3. The agent applies changes and commits its progress
4. Return to step 1

**Convergence signal:** A shrinking volume of modifications across successive passes — the diff gets smaller each time until only cosmetic changes remain. You are looking for diminishing returns, not absolute zero.

**When the loop isn't stabilizing, the problem is upstream — fix the inputs (specs, validation, coordination), not the iteration count.**

If the diff is not shrinking between runs:
- Kits are ambiguous (agents interpret them differently each time)
- Validation criteria are too loose (the agent has no way to confirm it got things right)
- Multiple agents are overwriting each other's work (ownership boundaries are unclear)

---

## Cross-References to Sub-Skills

Cavekit is composed of techniques that work together. This methodology skill is the index — each sub-skill below is self-contained but cross-references others.

### Foundation Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `ck:cavekit-writing` | Write implementation-agnostic kits with testable acceptance criteria | Draft phase — always the first step |
| `ck:context-architecture` | Organize context for progressive disclosure | Project setup and ongoing maintenance |
| `ck:impl-tracking` | Track implementation progress, dead ends, test health | Build and Inspect phases |
| `ck:validation-first` | Design validation gates agents can execute | All phases — validation is continuous |

### Pipeline Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `ck:prompt-pipeline` | Design numbered prompt pipelines for the Hunt | Setting up automation |
| `ck:revision` | Trace bugs back to kits and fix at the source | Inspect phase — after finding gaps |
| `cavekit:brownfield-adoption` | Adopt Cavekit on existing codebases | Starting Cavekit on legacy projects |

### Advanced Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `ck:peer-review` | Use a second agent to challenge the first | Quality gates, architecture review |
| `cavekit:speculative-pipeline` | Stagger pipeline stages for parallelism | Optimizing long pipelines |
| `ck:convergence-monitoring` | Detect convergence vs ceiling | Monitoring iteration loops |
| `cavekit:documentation-inversion` | Turn documentation into agent-consumable skills | Library/module documentation |

### Integration with Existing Skills

Cavekit works **with** existing skills, not as a replacement:

| Existing Skill | Cavekit Integration |
|----------------|-----------------|
| `superpowers:brainstorming` | Use during cavekit generation to explore requirements |
| `superpowers:writing-plans` | Use during plan generation for structured planning |
| `superpowers:test-driven-development` | TDD-within-Cavekit: cavekit acceptance criteria become failing tests |
| `superpowers:verification-before-completion` | Use for gate validation in every phase |
| `superpowers:executing-plans` | Use during implementation phase |
| `superpowers:dispatching-parallel-agents` | Use for agent team coordination |

---

## Quick Start

### For a New Project (Greenfield)

1. **Set up context directory:**
   ```
   context/
   ├── refs/           # Source materials (PRDs, language specs, research)
   ├── kits/     # Implementation-agnostic kits
   ├── plans/          # Framework-specific implementation plans
   ├── impl/           # Living implementation tracking
   └── prompts/        # Hunt pipeline prompts
   ```

2. **Write kits** from your reference materials (see `ck:cavekit-writing`)
3. **Generate plans** from kits (see `ck:prompt-pipeline`)
4. **Implement** with validation gates (see `ck:validation-first`)
5. **Track progress** in implementation documents (see `ck:impl-tracking`)
6. **Iterate** — when gaps are found, revise kits (see `ck:revision`)

### For an Existing Project (Brownfield)

1. **Set up context directory** (same structure as above)
2. **Designate existing codebase as reference material**
3. **Generate kits from code** (see `cavekit:brownfield-adoption`)
4. **Validate kits match behavior** — run tests against generated kits
5. **Proceed with normal Hunt** — future changes flow through kits first

---

## Summary

Cavekit is not a tool — it is a methodology. The core loop is simple:

1. **Describe what you want** (kits with testable criteria)
2. **Let agents build it** (plans → implementation → validation)
3. **Fix the kits, not the code** (revision)
4. **Repeat until converged** (iteration loops)

Agents become more capable the more precisely you constrain them — clear kits, automated validation, and structured iteration loops let them operate with increasing autonomy. None of this eliminates the need for software engineers. Your judgment on architecture, your ability to write precise kits, and your instinct for what "done" looks like are the inputs that make the whole system function. Cavekit is a force multiplier: one engineer's clarity of thought, scaled across an entire implementation pipeline.
