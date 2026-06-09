---
name: Primitive
kind: primitive
status: tracer
see-also: [slice, anti-pattern, entry]
---
# Primitive

An atomic capability that the repo ships and that a Slice composes. The
nouns of the working surface — what an agent can actually invoke.

## Definition

A Primitive is one of:

- a skill under `skills/<name>/`
- a hook script under `hooks/<name>.sh` (registered in `hooks/hooks.json`)
- a CLI command or subcommand exposed by the `ao` binary
- an eval suite under `evals/agentops-core/<name>.json`
- a documented contract under `docs/contracts/` or `schemas/`

Primitives are atomic in the sense that the repo ships them as one unit and
agents invoke them as one unit. They are NOT atomic in implementation — a
skill may have many references, a CLI command many flags.

## When to use

- When designing or auditing a feature, enumerate the Primitives it touches.
  If a feature lives in one Primitive only, it is probably under-integrated.
- When writing a Slice, the Slice is defined as the sequence of Primitives
  it crosses.

## Anti-pattern

- **Half-built Primitives.** A skill with no `SKILL.md` description, a CLI
  command with help text that does not match behavior, a hook registered in
  `hooks.json` but missing the script file. Each is a Primitive that lies
  about its own existence.
- **Primitive sprawl without an Index.** When the count of skills, hooks, or
  CLI commands grows past what an operator can hold in memory, and there is
  no Index entry under `skills/domain/references/` describing them as a
  cohort, the surface decays into a junk drawer.

## Example in this codebase

- The `ao eval run` CLI subcommand is one Primitive.
- The `agentops:rpi` skill is one Primitive.
- The `precompact-snapshot.sh` hook is one Primitive.
- The `evals/agentops-core/skill-quality-gates.json` suite is one Primitive
  (it ships, it is invoked atomically, it contracts behavior).

## See also

- `slice.md` — what composes Primitives end-to-end
- `anti-pattern.md` — common failure modes specific to Primitives
- `entry.md` — when a Primitive needs a corpus Entry to document its
  vocabulary role
