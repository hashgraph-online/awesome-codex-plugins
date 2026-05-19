# Strict Delegation Contract (shared)

> Applies to all top-level orchestrator skills: `/rpi`, `/discovery`, `/validation`.
> Strict sub-skill delegation is the **default**, not opt-in.

## The Contract

Top-level orchestrator skills delegate to their declared sub-skills via `$<skill>` invocations — **as separate tool invocations**, one per phase/step. Each sub-skill owns its artifact, its gate, and its retry policy. Inlining the work breaks that ownership chain.

There is no `--full` flag because strict delegation is always on.

## Phase-Isolated Transport

Strict delegation names the contract. Transport isolation names where that
contract runs.

For high-cost lifecycle phases, the desired runtime shape is:

1. The visible orchestrator keeps the lifecycle objective, phase order, and
   retry policy.
2. A phase runner receives only the phase skill name, the bounded handoff
   artifact, and the minimum objective context.
3. The runner executes the declared skill contract (`$discovery`, `$crank`, or
   `$validation`) in an isolated phase context.
4. The orchestrator receives only artifact path, verdict, and next action.

This is not a compression escape. It is strict delegation over an isolated
transport. The forbidden move is replacing the skill contract with direct
sub-agent work.

## Anti-Pattern: Compression

Do not inline phase work, compress multiple phases into one pass, substitute
direct Codex sub-agent work for `$<skill>` invocations, or skip mandatory
phases. Typical rationalizations to reject:

- *"I'll compress the three phases into one pass."*
- *"Let me do discovery inline — I already know what to do."*
- *"Nested `$<skill>` calls waste context; I'll spawn a Codex sub-agent instead."*
- *"The implementation is validated by tests passing; skipping `/validation`."*
- *"The plan looks good, skipping pre-mortem to save time."*
- *"I'll just spawn 3 judges directly — it's what `/vibe` does anyway."*
- *"Post-mortem is just writing a summary, I'll do it inline."*

All of these are contract violations. A live compression was observed 2026-04-19 (see [`docs/learnings/orchestrator-compression-anti-pattern.md`](../../../docs/learnings/orchestrator-compression-anti-pattern.md)). The compression "worked" mechanically (strict build passed, 2-judge inline vibe PASSed) but the knowledge flywheel never turned — no forged learnings, no post-mortem artifact, no structured council verdict. Contract strength depends on actual `$<skill>` invocations, not self-certification.

## Codex sub-agents vs `$<skill>` invocations

These are **not interchangeable**:

| Call | When to use |
|------|-------------|
| `$<skill> <args>` | Invoking a declared skill with its full contract. Required for phase delegation. |
| Codex sub-agent (e.g., `explorer` role) | Spawning a sub-agent for parallel independent work **within a skill's step** (e.g., `/research` dispatching parallel explorer sub-agents is fine). |
| Phase runner | Runtime transport that executes one declared skill contract in an isolated context and returns only the bounded phase artifact. |

If you're tempted to spawn a Codex sub-agent in place of a `$<skill>` invocation, you're compressing. Stop.

If Codex lacks a native skill-fork boundary, a phase runner may use a sub-agent,
daemon job, or process wrapper as transport. That wrapper must be thin: load
the declared skill, execute the skill workflow, write the expected artifact,
and return a compact result. It must not perform the phase directly.

## Supported Compression Escapes

These flags scale *gate depth* or *scope*, **never skip phases**. They are the only supported shortcuts:

### `/rpi`
- `--quick` / `--fast-path` — force fast complexity (inline `--quick` gates inside sub-skills; still runs all three phases)
- `--from=<phase>` — resume from a specific phase when earlier artifacts already exist
- `--skip-pre-mortem` / `--no-retro` / `--no-forge` — skip specific sub-skills inside a phase
- `--no-budget` — disable phase time budgets

### `/discovery`
- `--quick` — passed through to `/pre-mortem` for fast inline gate
- `--skip-brainstorm` — skip STEP 1 when the goal is specific (>50 chars, no vague keywords)
- `--interactive` / `--auto` — control human-gate behavior in research and plan
- `--no-scaffold` — skip STEP 4.5 scaffold auto-invocation (canonical name; `--no-lifecycle` is a deprecated alias through v2.40.0)

### `/validation`
- `--quick` — fast inline gates inside sub-skills (vibe, post-mortem)
- `--no-retro` / `--no-forge` — skip specific sub-skills
- `--no-lifecycle` — skip STEP 1.7 lifecycle checks (test, deps, review, perf)
- `--no-behavioral` — skip STEP 1.8 holdout scenarios
- `--allow-critical-deps` — allow shipping despite CVSS ≥ 9.0 findings

**If tempted to shortcut outside this list: stop and delegate.**

## Positive Pattern: What Correct Delegation Looks Like

A correct `/rpi` invocation shows three distinct `$<skill>` invocations at phase boundaries:

```
$discovery <goal> --auto      # Phase 1
  → <promise>DONE</promise>
  → reads .agents/rpi/execution-packet.json
$crank <packet-path> [--test-first]   # Phase 2
  → <promise>DONE</promise>
  → reads .agents/rpi/phase-2-summary-*.md
$validation --complexity=<level> [--strict-surfaces]   # Phase 3
  → <promise>DONE</promise>
  → writes .agents/rpi/phase-3-summary-*.md
```

Anything less is compressed.

When phase-isolated transport is available, the transcript may show a phase
runner instead of raw inline skill execution. The acceptance rule is still the
same: the delegated phase contract must run, emit its completion marker, and
write the expected phase summary file.

## Detection for Reviewers

When auditing a session that claims to have run `/rpi`, check the transcript for:

1. **Three delegated phase contracts** at phase boundaries (`$<skill>` directly,
   or a phase runner whose sole job is to execute the named skill contract).
2. **Three `<promise>DONE</promise>` markers**, each from the delegated sub-skill.
3. **Three phase summary files** in `.agents/rpi/phase-{1,2,3}-summary-*.md`.

Missing any of the three = compression.

## Enforcement Layers (defense in depth)

1. **This contract document** — read before / during orchestrator invocation.
2. **Loud text in each orchestrator's SKILL.md** — anti-pattern section with explicit examples.
3. **Durable learning** at `docs/learnings/orchestrator-compression-anti-pattern.md` — surfaced through the orchestrator skill contracts.
4. **Optional future**: runtime hook that inspects the skill invocation trace and blocks downstream work when phases were skipped. Not implemented; deferred to a follow-up initiative.

Contract strength alone is not enforcement. Layer 1 (this doc) + Layer 2 (SKILL.md sections) + Layer 3 (flywheel injection) together give durable coverage.
