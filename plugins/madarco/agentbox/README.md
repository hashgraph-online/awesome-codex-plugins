# AgentBox — Codex plugin

Drive AgentBox from [Codex](https://openai.com/index/introducing-codex/) on the host:
create isolated sandboxes for coding agents, run them in parallel, queue background jobs,
and push commits safely through the host relay.

## Install

```bash
codex plugin marketplace add madarco/agentbox
codex plugin add agentbox@agentbox
```

This repo doubles as a single-plugin Codex marketplace: `.agents/plugins/marketplace.json`
points at this bundle (`./plugins/agentbox`).

## Layout

```
plugins/agentbox/
  .codex-plugin/plugin.json   # manifest (skills + composerIcon resolve from this dir's parent)
  assets/icon.svg
  skills/agentbox-info/SKILL.md
```

`skills/agentbox-info/SKILL.md` is a **real copy** of the canonical skill at
`apps/cli/share/host-skills/agentbox-info/SKILL.md` — Codex copies the bundle on install and
does not follow a symlink that points outside it, so the content must live here directly.
A CI guard (`pnpm check:plugin-skill`) fails if the copy drifts; run
`node scripts/check-plugin-skill-sync.mjs --fix` to resync after editing the canonical skill.
