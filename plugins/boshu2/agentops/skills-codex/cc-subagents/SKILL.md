---
name: cc-subagents
description: Run managed subagents.
---

# cc-subagents (Codex)

Codex-native parity wrapper. The full skill content — overview, the five critical
constraints (no per-token API billing, non-overlapping file ownership, fresh
context per worker, least-tools/read-only by default, evidence-gated "done"), the
four-phase workflow (decide → pick role profile → spawn → SubagentStop/collect),
the role-profile table, output spec, quality rubric, examples, and
troubleshooting — lives in the sibling base file `../SKILL.md`. Read it first.

Codex execution steps and guardrails for this skill are in `prompt.md` (same dir).
