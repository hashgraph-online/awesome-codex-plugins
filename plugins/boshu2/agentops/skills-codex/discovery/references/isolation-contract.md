# Phase Skill Isolation Contract

How RPI keeps phase skills (`$discovery`, `$crank`, `$validation`) from
compressing each other's work into one agent context while preserving strict
delegation and operator visibility.

## Declaration vs Enforcement

**Declaration.** [`PRODUCT.md`](../../../PRODUCT.md) operational principle #5
(two-tier execution) declares that phase skills own their own phase artifacts,
gates, and retry policies. `$rpi` owns the lifecycle objective and phase order,
not the internals of discovery, implementation, or validation.

**Enforcement.** This document plus
[`scripts/check-skill-isolation.sh`](../../../scripts/check-skill-isolation.sh)
enforce the authored contract by detecting compression patterns in phase-skill
SKILL.md bodies. Runtime isolation is a separate transport concern: when a
runtime supports phase-isolated transport, the orchestrator gives a phase
runner only the lifecycle objective, the bounded execution packet path, and the
phase skill name. The runner executes that declared phase contract and returns
only the phase artifact, verdict, and next action.

**Important distinction.** A subagent, daemon job, or spawned process may be a
transport for a declared skill contract. It must not become a replacement for
the skill. "Run `$discovery` in an isolated phase context" preserves strict
delegation. "Skip `$discovery` and have an agent research/plan directly" is
compression.

The companion
[`shared/references/strict-delegation-contract.md`](../../shared/references/strict-delegation-contract.md)
gives the human-readable rationale and canonical anti-pattern catalogue. Read
this file for the mechanical contract; read that one for the philosophy.

## Four Levers

These are the four mechanical levers available to keep phase contexts bounded.
They are listed in increasing strength, with the recommended posture last.

| Lever | Description | Mechanical strength |
|---|---|---|
| A | Text contract in SKILL.md and this reference | Weak - relies on agent compliance |
| B | Static lint via `scripts/check-skill-isolation.sh` | Medium - catches authored compression |
| C | Artifact-only handoff via `.agents/rpi/execution-packet.json` and phase summaries | Strong - limits what crosses phases |
| D | Phase-isolated skill transport | Strongest - phase context can die after the artifact returns |

**Recommended posture: D with A-C always on.** Layered enforcement keeps the
contract durable when any single lever weakens. Text drifts, lint only sees
source files, artifact handoffs can be overstuffed, and transport can be
implemented incorrectly. Together they preserve the narrow waist: phase skill
contract in, bounded artifact out.

## Compression Patterns

The lint script (`scripts/check-skill-isolation.sh`) flags the following
patterns inside phase-skill SKILL.md bodies
(`skills/{rpi,discovery,crank,validation}/SKILL.md`):

1. **Cross-phase first-person verbs.** Phrases like `I will research`, `I will
   plan`, `I will crank`, `I will validate` (case-insensitive). A phase skill
   should not describe itself as doing another phase's work.
2. **Inline research vocabulary.** Phrases like `let me grep`, `let me read`,
   `let me search`, `I'll grep`, `I'll read`, `I'll search`
   (case-insensitive). These signal that the agent intends to inline
   research-phase work into the current context instead of delegating.
3. **Phase-skill calling another phase skill.** A `$research`, `$plan`,
   `$crank`, or `$validation` callsite inside a phase-skill SKILL.md, except
   for the legitimate orchestration patterns:
   - `$rpi` legitimately orchestrates `$discovery`, `$crank`, `$validation`
     (this is its core contract). It should not call `$research` or `$plan`
     directly; those are discovery's sub-skills.
   - `$discovery` legitimately orchestrates `$research` and `$plan`. It should
     not call `$crank` or `$validation`; those are downstream phases.
   - `$crank` should not call `$research`, `$plan`, `$crank`, or `$validation`;
     phase 2 is sealed.
   - `$validation` should not call `$research`, `$plan`, `$crank`, or
     `$validation`; phase 3 is sealed.

## Mechanical Enforcement

Three surfaces, layered:

1. **Lint.**
   [`scripts/check-skill-isolation.sh`](../../../scripts/check-skill-isolation.sh)
   walks `skills/{rpi,discovery,crank,validation}/SKILL.md` and exits
   non-zero on compression patterns. Run `--self-test` to assert a known
   violation is caught.
2. **Artifact handoff.** [`phase-data-contracts.md`](phase-data-contracts.md)
   defines the bounded files that may cross phase boundaries. Raw reasoning
   does not cross phases.
3. **Phase-isolated skill transport.** When the runtime can isolate phase
   execution, RPI should run each phase contract in a fresh phase context and
   keep the main orchestrator visible.

## See Also

- [`docs/learnings/orchestrator-compression-anti-pattern.md`](../../../docs/learnings/orchestrator-compression-anti-pattern.md)
- [`skills/rpi/references/phase-data-contracts.md`](phase-data-contracts.md)
