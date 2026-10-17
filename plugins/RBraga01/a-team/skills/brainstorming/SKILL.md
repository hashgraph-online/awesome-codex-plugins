---
name: brainstorming
description: Use BEFORE any creative work — creating features, building components, adding functionality. Explores user intent, requirements, and design before implementation. Hard-gated: no code until user approves the spec.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

<HARD-GATE>
Do NOT write any code, scaffold any project, or take any implementation action until you have
presented a design and the user has explicitly approved it. This applies to EVERY project
regardless of perceived simplicity.
</HARD-GATE>

## Checklist (Complete in Order)

1. **Explore project context** — check files, docs, recent commits
2. **Offer visual companion** (if visual questions ahead) — own message, not combined
3. **Ask clarifying questions** — one at a time: purpose, constraints, success criteria
4. **Propose 2-3 approaches** — with trade-offs and your recommendation
5. **Present design** — scaled to complexity, get approval section by section
6. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md` and commit
7. **Spec self-review** — scan for placeholders, contradictions, ambiguity, scope
8. **User reviews spec** — wait for user approval before proceeding
9. **Transition** — invoke `writing-plans` skill to create implementation plan

## Key Principles

- **One question at a time** — never multiple questions in one message
- **Multiple choice preferred** — easier to answer than open-ended
- **YAGNI ruthlessly** — remove unnecessary features from all designs
- **Explore alternatives** — always propose 2-3 approaches before settling
- **Incremental validation** — present design sections, get approval before moving on

## After the Design

- Write spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Run spec self-review (check: placeholders? contradictions? scope? ambiguity?)
- Ask user to review and approve spec
- Invoke `writing-plans` skill — not any other skill

**The terminal state is invoking writing-plans. Do NOT invoke any implementation skill.**

## Spec Self-Review Checklist

1. Any "TBD" or incomplete sections? Fix them.
2. Do sections contradict each other? Resolve.
3. Is this focused enough for a single plan, or needs decomposition?
4. Can any requirement be interpreted two ways? Pick one and make it explicit.
