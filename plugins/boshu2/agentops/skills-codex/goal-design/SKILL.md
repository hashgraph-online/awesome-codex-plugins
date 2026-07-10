---
name: goal-design
description: Create validated goal-design packets.
---
# $goal-design — Validated Intent Packet Authoring

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), run:

```bash
ao codex ensure-start 2>/dev/null || true
```

The CLI records startup once per thread and skips duplicates automatically.

> **Loop position:** pre-discovery adapter for move 1 of the operating loop.
> It turns a human goal into a checked `intent.md` + `driver.md` packet that
> `$discovery` and `$plan` can consume without relying on chat context.

**Execute this workflow. Do not only describe it.**

## Purpose

Use `$goal-design` when the goal is important enough to leave chat but not yet
ready to become beads. The skill writes `.agents/goal-design/<slug>/intent.md`
and `driver.md`, refreshes the driver digest, runs the packet checker, and
requires an independent validation verdict before the packet drives work.

Do not use `$goals` for this. `$goals` maintains `GOALS.md` fitness specs;
`$goal-design` creates a per-objective intent packet.

## Inputs

Given `$goal-design "<goal>" [--slug <slug>]`:

| Input | Meaning |
| --- | --- |
| goal | Human objective to shape as BDD |
| `--slug` | Optional packet slug; default is kebab-case from goal |
| `--scenario-id` | Optional first scenario id; default `S1` |
| `--bounded-context` | Optional BC tag; default `bc-loop` until evidence says otherwise |

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

3. **Edit deliberately.** If you edit `intent.md`, refresh `driver.md` before
   checking:

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
7. **Emit the dispatch prompt.** When the packet executes out-of-session via a
   goal API (codex goals, claude goals, an NTM/ATM pane, `bushido spawn`),
   emit the small copyable prompt that points the worker at the packet:

   ```bash
   scripts/goal-design-packet.py prompt .agents/goal-design/<slug>
   ```

   Paste the output verbatim into the goal command. It fails closed on a
   draft packet (validate first; `--allow-draft` for a preview) and on prompts
   over 4000 characters (the codex goal-API limit). The packet files remain
   the contract of record; the prompt only aims the worker at them.

## Andon router (author it into driver.md)

A long autonomous run is only safe if the goal carries its own escalation
policy — a per-goal **class → tier** router, never a flat "escalate to me"
(doctrine: `docs/architecture/the-flywheel.md`, the three-tier andon). When
authoring `driver.md`, write the router as a table in the driver **body** and
mirror its escalation semantics in the schema-validated `route_back_rules`
frontmatter (auto → `validation_fails`, council →
`promotion_contradicts_intent`, human → a breaker-trip clause in those rules):

| One-way-door class | Tier | Machinery (reuse, never rebuild) |
| --- | --- | --- |
| Gate / validation failure | **auto** | AUTO-REDO + `ao gate check --fast --scope head` |
| Architecture fork / plan-shape one-way door | **council** | `$council` + `ao plan-pawl decide` (PASS/REDO/BLOCKED) + `$converge` |
| Money / legal / irreversible-external (the refusal lane) + any breaker trip | **human** | ESCALATE / HOLD — hand back to the operator |

Every router carries the implicit final row: a slice that cannot pass
validation in N rounds, an oscillation, or a scope-creep flag trips the
breaker to **human** — stop and ask, never guess through it.

**Schema limit (do not hack it):** the driver v1 schema is
`additionalProperties: false` with no dedicated andon field, so the class →
tier table lives in the driver body while `route_back_rules` carries the
machine-checkable semantics. A driver v2 `andon_router` field is a candidate
follow-up — do not modify the landed schemas, templates, or checker to add it.

## Output

- `.agents/goal-design/<slug>/intent.md`
- `.agents/goal-design/<slug>/driver.md`
- Checker output from `scripts/check-goal-design-packet.sh`
- Independent validation verdict path or summary
- Copyable dispatch prompt (`scripts/goal-design-packet.py prompt <packet>`)
  when a goal API executes the packet out-of-session

## Done

`$goal-design` is done only when:

1. The packet contains both required files.
2. `scripts/check-goal-design-packet.sh .agents/goal-design/<slug>` exits 0.
3. The independent validator returns `PASS` or `WARN` with no blocker.
4. The next action is explicit: `$discovery .agents/goal-design/<slug>`,
   `$plan .agents/goal-design/<slug>`, or an emitted dispatch prompt handed to
   a goal API (codex/claude goals).

## Scenarios

```gherkin
Feature: Goal-design packets carry validated intent into the loop
  Scenario: Create a checked packet before discovery
    Given a human objective that should not stay only in chat
    When $goal-design writes intent.md and driver.md
    Then scripts/check-goal-design-packet.sh passes
    And the packet names an independent validation verdict before $discovery or $plan consumes it

  Scenario: Reject stale or inconsistent packet identity
    Given driver.md points at stale, mismatched, or unknown intent content
    When the packet checker runs
    Then it exits non-zero before planning or implementation starts

  Scenario: Emit a dispatch prompt for goal APIs
    Given a validated goal-design packet
    When goal-design-packet.py prompt runs against it
    Then a copyable prompt under 4000 characters points the worker at intent.md and driver.md
    And a draft packet is refused unless --allow-draft is passed
```

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
