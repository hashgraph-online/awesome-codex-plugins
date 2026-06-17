---
name: account-rotation
description: Switch coding-agent accounts on a usage/rate limit, routed by host and agent.
---

# account-rotation (Codex)

Codex-native entry point for the `account-rotation` operator skill.

The AgentOps source skill `../../skills/account-rotation/SKILL.md` is the source
of truth for domain behavior, the host+agent routing table, capture discipline,
the live-session caveat, and swarm-lane spreading. Read it first, then use
`prompt.md` for the Codex runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Do not invoke Claude Code as an executor.
- Route by host+agent per the source skill's table; on this runtime the swap
  tool is `caam` (file-layer auth swap) for Codex/Gemini and Linux/WSL lanes.
- Load only the relevant source references or scripts for the task.
- Verify command syntax from local `--help` or checked-in references before acting.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.

## Navi-rotate (you rotate a builder peer)
In the trilateral, YOU (codex Navi) run on a different runtime, so a builder's rate
limit does not affect you — you rotate it: `navi-rotate <peer-tmux-session> [--to
<acct>] [--dry-run]` (`dotfiles/bin/navi-rotate`) picks the builder's next account,
swaps it, then am+atm-signals the peer to relaunch. The swap lands on the peer's
NEXT launch (live token unaffected); continuity rides worktree+bead. The account-swap
tool is the builder-runtime's concern (routed in the source skill).
