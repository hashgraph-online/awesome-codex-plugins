---
name: setup
description: 'Check whether Claude Code CLI is ready in this environment and optionally toggle the stop-time review gate. Args: --enable-review-gate, --disable-review-gate. Use for installation, authentication, or review-gate setup requests.'
---

# Claude Code Setup

Use this skill when the user wants to verify Claude Code readiness or toggle the review gate.

Resolve `<plugin-root>` as two directories above this `SKILL.md` file. Always run the companion from that active plugin root.

Supported arguments:
- `--enable-review-gate`
- `--disable-review-gate`

Workflow:
- First run the machine-readable probe:
  `node "<plugin-root>/scripts/claude-companion.mjs" setup --json $ARGUMENTS`
- If it reports that Claude Code is unavailable and `npm` is available, ask whether to install Claude Code now.
- If the user agrees, run `npm install -g @anthropic-ai/claude-code` and rerun setup.
- If Claude Code is already installed or `npm` is unavailable, do not ask about installation.
- If setup reports missing native plugin hook features or hook trust, rerun setup once. The companion repairs `[features].hooks`, `[features].plugin_hooks`, and this plugin's native hook trust hashes itself.
- After the decision flow is complete, run the final user-facing command without `--json`:
  `node "<plugin-root>/scripts/claude-companion.mjs" setup $ARGUMENTS`

Output:
- Present the final non-JSON setup output exactly as returned by the companion.
- Use the JSON form only for branching logic such as install or auth decisions.
- Preserve any authentication guidance if setup reports that login is still required.
