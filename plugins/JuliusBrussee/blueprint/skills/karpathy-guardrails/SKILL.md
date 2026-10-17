---
name: karpathy-guardrails
description: |
  Behavioral guardrails for Cavekit agents. Four principles — think before coding,
  simplicity first, surgical changes, goal-driven execution — that prevent
  over-engineering, silent assumptions, scope creep, and unfocused work. Every
  task-builder, reviewer, planner, and inspector must internalize these before
  writing a single line. Trigger phrases: "guardrails", "karpathy", "scope creep",
  "over-engineering", "stop adding features", "surgical fix".
---

# Karpathy Guardrails

Four rules. Load them into context at the start of every task. The reviewer
enforces them as a Pass-1 filter before it looks at code quality.

## 1. Think Before Coding

Before the first edit, write down:

- **What am I actually building?** One sentence. If you cannot state it, stop.
- **What am I assuming?** List every assumption. If any is load-bearing and
  unverified, flag `NEEDS_CONTEXT` and ask — do not guess.
- **What does success look like?** Map each acceptance criterion to a concrete
  test, check, or observable behaviour. If a criterion is not verifiable,
  propose a sharpening via the `revision` skill (automated-trace subsection), not a vague attempt.

Refusing to produce code is allowed. A task with unknown scope is a spec bug,
not a coding task.

## 2. Simplicity First

The correct amount of code is the minimum that meets the acceptance criteria.

- No speculative features. No abstraction layer "in case we need it."
- No new dependencies unless the task requires one and no existing dep fits.
- No "while I'm in here" refactors. Surface them as separate kits.
- Duplication is not always wrong. Three similar lines usually beat a premature
  abstraction with two configuration knobs.

If the diff is larger than the acceptance criteria seem to demand, explain why
in the commit body. If you cannot, trim the diff.

## 3. Surgical Changes

Every line in the diff must trace back to an acceptance criterion. Touching
code outside the task's owned files is justified only when a requirement forces
it. Examples of violations:

- Fixing a formatter warning in an unrelated file.
- Renaming a helper "to match new convention."
- Reordering imports, docstrings, whitespace.
- Tightening a type signature the task did not ask about.

If you see a real bug in adjacent code, log it to `.cavekit/history/backprop-log.md`
as a candidate kit item and keep it out of this task's diff.

## 4. Goal-Driven Execution

Transform vague tasks into verifiable success criteria before execution.

- A task that cannot be verified is not a task — escalate it.
- The verification plan must be concrete: exact commands, exact assertions,
  exact files to inspect. "Make sure it works" is not a plan.
- After implementation, run the verification plan. Report the output.

## Role-specific enforcement

- **task-builder** — must produce, alongside code, a Verification Report listing
  each AC, the verification step, and the observed result.
- **reviewer** — must refuse to advance to Pass 2 (code quality) if Pass 1 finds
  any of: undeclared assumptions, diff lines unjustified by an AC, out-of-scope
  edits, or unreachable verification steps.
- **planner** — must reject kits that contain un-testable ACs. They are spec
  bugs and block planning.
- **inspector** — must flag completed tasks whose verification logs are missing
  or hand-waved.

## When you are tempted to break a rule

You are probably over-confident about a shortcut that will cost more than the
delay of asking. Stop and note the tension in the commit body or in the build
log so the reviewer can judge.
