# autodev

Manage `$autodev` as the Codex-facing operator surface for the repo-local
`PROGRAM.md` or `AUTODEV.md` autonomous development contract.

## Codex Execution Profile

1. Treat `skills/autodev/SKILL.md` as the source contract and
   `skills-codex/autodev/SKILL.md` as the Codex-facing artifact.
2. Run `ao codex ensure-start 2>/dev/null || true` before editing or validating
   a program contract in Codex hookless mode.
3. Use `ao autodev validate --json` as the structural gate before passing work
   to `$evolve` or `$rpi`. Do not shell out to a retired CLI wrapper as the Codex
   handoff path unless the user explicitly asks for a terminal wrapper.
4. Keep the distinction explicit: `autodev` defines the loop contract, `evolve`
   runs the autonomous loop, and `rpi` runs one lifecycle.
5. When the requested work falls outside immutable scope, create or update a bead
   instead of silently widening the contract.

## Guardrails

1. Prefer `PROGRAM.md` over `AUTODEV.md` when both exist.
2. Do not invent broad mutable scope; infer it from repo context or keep it
   narrow.
3. Do not mark a cycle successful until the program validation bundle and stop
   conditions are satisfied.
