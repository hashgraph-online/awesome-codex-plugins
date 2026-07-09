# goal-design

Create a schema-backed `.agents/goal-design/<slug>/` packet for Codex, refresh
the digest with `scripts/goal-design-packet.py`, run the packet checker, then
route the checked packet to `$validate` before it drives `$discovery` or `$plan`.


<!-- BEGIN AGENTOPS OPERATOR CONTRACT -->
<!-- Generated from skills-codex-overrides/catalog.json for goal-design. -->

## Codex Execution Profile

1. In Codex hookless mode, run `ao codex ensure-start` before authoring.
2. Use `scripts/goal-design-packet.py` for new packets and digest refreshes.
3. Run `scripts/check-goal-design-packet.sh` before handoff.

## Guardrails

1. Do not confuse goal-design packets with `GOALS.md` fitness goals.
2. Preserve scenario ids and names when handing to `$discovery` or `$plan`.

<!-- END AGENTOPS OPERATOR CONTRACT -->
