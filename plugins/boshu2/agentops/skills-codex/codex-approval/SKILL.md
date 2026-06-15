---
name: codex-approval
description: "Ask an ATM Fable validator for Codex approval."
---

# codex-approval (Codex)

Codex-native parity wrapper. The full skill content — constraints, workflow,
artifact contract, quality rubric, and troubleshooting — lives in the sibling
base file `../SKILL.md`. Read it first.

For fanout discovery, Fable reviews the `SynthesisPacket` plus every
`PerspectivePlan` and Codex persists an `ApprovalEdge` with the tmux capture and
normalized verdict. `WARN is not` a silent pass.

Codex execution steps and guardrails for this skill are in `prompt.md` (same dir).
