---
name: goal-design
description: "Create validated goal-design packets."
---
# $goal-design — Validated Intent Packet Authoring

> **Loop position:** pre-discovery adapter for move 1 of the operating loop.
> It turns a human goal into a checked `intent.md` + `driver.md` packet that
> `$discovery` and `$plan` can consume without relying on chat context.

**Execute this workflow. Do not only describe it.**

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), run:

```bash
ao codex ensure-start 2>/dev/null || true
```

## Purpose

Use `$goal-design` when the goal is important enough to leave chat but not yet
ready to become beads. The skill writes `.agents/goal-design/<slug>/intent.md`
and `driver.md`, refreshes the driver digest, runs the packet checker, and
requires an independent validation verdict before the packet drives work.

Do not use `$goals` for this. `$goals` maintains `GOALS.md` fitness specs;
`$goal-design` creates a per-objective intent packet.

## Workflow

1. **Shape WHAT before HOW.** Write the objective, why, bounded context,
   non-goals, rollback/containment, stale assumptions, and at least one
   Given/When/Then scenario.
2. **Create the packet with the helper.** Prefer the digest-safe tool:

   ```bash
   scripts/goal-design-packet.py new <slug> \
     --objective "<goal>" \
     --scenario-name "<observable behavior>" \
     --first-failing-proof "<test or command>" \
     --write-scope "<path or glob>"
   ```

3. **Refresh after edits.** If you edit `intent.md`, run:

   ```bash
   scripts/goal-design-packet.py refresh-digest .agents/goal-design/<slug>
   ```

4. **Run the deterministic checker.**

   ```bash
   scripts/goal-design-packet.py check .agents/goal-design/<slug>
   ```

   The checker must fail closed on stale digest, slug drift, misleading
   `intent_ref.path`, unknown scenario ids, unmapped candidate behavior, schema
   violations, and self-grading language.

5. **Get independent validation.** Invoke `$validate .agents/goal-design/<slug>`
   or an equivalent fresh-context validator. A checker-clean packet with no
   independent verdict is not ready to drive work.

6. **Hand off.** After validation, pass the packet path to `$discovery` or
   `$plan`. Preserve scenario ids and names exactly; do not paraphrase `S1`,
   `S2`, or candidate behavior labels away.

## Done

`$goal-design` is done only when:

1. The packet contains both required files.
2. `scripts/check-goal-design-packet.sh .agents/goal-design/<slug>` exits 0.
3. The independent validator returns `PASS` or `WARN` with no blocker.
4. The next action is explicit: `$discovery .agents/goal-design/<slug>` or
   `$plan .agents/goal-design/<slug>`.

## Non-Goals

- Do not add or edit `GOALS.md`.
- Do not create beads directly unless `$plan` is invoked.
- Do not add a dedicated Goal Design CLI command until this skill proves repeated use.
- Do not track generated repo-root `.agents/goal-design` packets unless the
  write-surface contract changes.

## Validation

```bash
bats tests/scripts/goal-design-packet.bats
bats tests/scripts/check-goal-design-packet.bats
scripts/check-goal-design-packet.sh .agents/goal-design/<slug>
```
