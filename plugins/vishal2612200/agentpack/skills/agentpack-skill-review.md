---
name: agentpack-skill-review
description: Review an existing agent skill and generate a balanced trigger/non-trigger eval set with a reproducible iteration workspace. Use when improving, benchmarking, or checking whether a SKILL.md triggers correctly.
---

# AgentPack Skill Review

Use when the user invokes `$agentpack-skill-review <skill path or name>` or asks to review, improve, benchmark, or generate evals for a skill.

## Workflow

1. Run `agentpack skill-review --skill "$ARGUMENTS" --json` and read the generated `review.md`, `findings.json`, and `evals.json`.
2. Inspect the target `SKILL.md` directly. Treat the deterministic findings as evidence-backed checks, not a complete quality judgment.
3. Review the candidate eval set. Keep an even split of realistic should-trigger and near-miss should-not-trigger queries; edit or add cases when the generated wording is artificial.
4. Run the evals against both the current skill and a baseline without the skill when the host can run isolated agent tasks. Store transcripts, outputs, timing, and token metadata under the workspace's next `iteration-N/` directory.
5. Grade objective assertions programmatically where possible and record human feedback separately. Compare trigger precision/recall, output quality, latency, and token cost.
6. Propose targeted changes to `SKILL.md` and rerun the same evals as a new iteration. Do not claim improvement from a single example or from generated candidates that the user has not reviewed.
7. Report the workspace paths, findings, eval-set balance, baseline comparison, and validation status. If a browser viewer is available, use the host's standard eval viewer rather than writing a custom one.

The CLI command only writes local artifacts. It does not call a hosted model API or edit the skill automatically.
