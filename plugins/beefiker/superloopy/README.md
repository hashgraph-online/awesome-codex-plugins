<div align="center">

# 🌀 Superloopy

**Loop engineering for Codex.** Type `loopy <task>` — an agent does the work, proves each piece with real evidence, and only then says it's done.

<p>
  <a href="README.md">English</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.zh-CN.md">中文(简体)</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

<img src=".github/assets/franky.png" width="92" alt="franky" />&nbsp;<img src=".github/assets/zoro.png" width="92" alt="zoro" />&nbsp;<img src=".github/assets/usopp.png" width="92" alt="usopp" />&nbsp;<img src=".github/assets/jinbe.png" width="92" alt="jinbe" />&nbsp;<img src=".github/assets/robin.png" width="92" alt="robin" />&nbsp;<img src=".github/assets/nami.png" width="92" alt="nami" />

<sub><b>the crew</b> — optional subagents, one job each</sub>

</div>

## Use it

After installing, type your task in Codex with a leading `loopy`:

```
loopy fix the failing login test and prove it with evidence
```

The agent plans it, proves each piece with a real file, and reports back — you don't run any commands yourself. The packaged Stop hook stays quiet unless `SUPERLOOPY_STOP_HOOK=on`.

## Why Superloopy?

Superloopy is for Codex work where "done" needs to mean more than a confident status sentence.

- Evidence-first: every pass points at a real artifact under `.superloopy/evidence/`.
- Lightweight by default: one small CLI, repo-local state, zero runtime dependencies.
- Agent-friendly: skills, hooks, and optional crew lanes guide Codex without hiding the final gate.

## Skills

Superloopy keeps the command layer small. Skills carry the specialist workflow: when to use it, what the agent should inspect, and what proof must be left under `.superloopy/evidence/`.

| Skill | Use it when | What it produces |
| --- | --- | --- |
| `superloopy-loop` | You type `loopy <task>` or `loopy team <task>` for a full loop; use `loopywork`, `lpy`, or `$lpy` for guidance-only context. | Full loops produce a lightweight plan, guided next actions, command-backed proof, a quality gate, and a final evidence report. Guidance aliases do not mutate state. |
| `superloopy-research` | You ask for `loopy research`, deep research, exhaustive investigation, or a cited report. | Research axes, expansion waves, a claim ledger, verification notes, and a cited synthesis artifact. |
| `superloopy-clone` | You ask for `loopy clone`, authorized website cloning, rebuilding, migration, or pixel-focused page recovery. | Browser captures, page topology, design tokens, asset inventory, implementation notes, build output, and visual QA evidence. |
| `superloopy-frontend` | You build, style, or redesign any UI/page/component, or ask to make something look designed (auto-activates on visual work). | A DESIGN.md token contract, an anti-slop pre-flight result, and a real-browser visual-QA evidence artifact. |

The loop skill is the default guardrail. `loopy` starts or resumes the evidence loop; `loopy team` escalates to crew mode. `loopywork`, `lpy`, and `$lpy` only inject starter guidance. Research and clone are opt-in specialist modes, and both still finish by recording Superloopy evidence instead of trusting a status sentence.

## Clone Demo

[![Transferloom.com clone reference](.github/assets/transferloom-clone-reference.png)](https://transferloom.com/)

`superloopy-clone` reproduced Transferloom.com locally and passed desktop/mobile browser validation. The reference run preserved the sticky nav, animated hero, app preview sections, comparison table, security panel, sister app banner, footer, local assets, and Superloopy evidence trail.

## The crew

For bigger work, Superloopy ships six optional subagents under `.codex/agents/` — each owns one lane. They install automatically with the plugin (no command needed); `superloopy agents install` just re-copies them if you ever need it. Their advisory model defaults are documented in `docs/superloopy-model-policy.md` and checked by `superloopy doctor`.

<table>
  <tr>
    <td align="center" width="33%"><img src=".github/assets/franky.png" width="190" alt="franky" /><br /><b>franky</b><br /><sub>builds it</sub></td>
    <td align="center" width="33%"><img src=".github/assets/zoro.png" width="190" alt="zoro" /><br /><b>zoro</b><br /><sub>reviews it</sub></td>
    <td align="center" width="33%"><img src=".github/assets/usopp.png" width="190" alt="usopp" /><br /><b>usopp</b><br /><sub>tests it</sub></td>
  </tr>
  <tr>
    <td align="center"><img src=".github/assets/jinbe.png" width="190" alt="jinbe" /><br /><b>jinbe</b><br /><sub>gates it</sub></td>
    <td align="center"><img src=".github/assets/robin.png" width="190" alt="robin" /><br /><b>robin</b><br /><sub>audits it</sub></td>
    <td align="center"><img src=".github/assets/nami.png" width="190" alt="nami" /><br /><b>nami</b><br /><sub>finds it</sub></td>
  </tr>
</table>

**Summon the crew** with `loopy team <task>` — or `loopy crew`, the one-word `loopycrew`, or just `ultrawork <task>`. Superloopy fans the work out across the lanes in parallel and still proves every piece before it calls it done. A plain `loopy <task>` stays solo and only delegates when the slices are clearly independent.

For full crew runs, the parent records each lane with `superloopy loop handoff`, checks `superloopy loop fleet --json`, and keeps the human final gate report separate from the machine gate JSON. A gate report can be Markdown evidence; `superloopy loop finish --artifact` is for `.json` quality gate output.

When a tracked crew handoff finishes, Superloopy can print one original crew line before the normal `handoff` or `fleet` status. It follows the user's language from the assignment or scoped brief when it matches the supported catalog, with English as the safe fallback. The line is personality only; the verdict, evidence artifact, outstanding list, and attention list stay authoritative.

## Install

Needs Node.js ≥ 20 and Codex CLI ≥ 0.131.0 for `codex plugin add`. Superloopy is dependency-free — zero runtime dependencies, just Node.

```
codex plugin marketplace add https://github.com/beefiker/superloopy
codex plugin add superloopy@beefiker
```

Restart Codex after installing the plugin. If Codex asks you to review hooks, approve them; the next approved session runs a `SessionStart` hook that does a one-time bootstrap — it installs the `superloopy` command and the agents. If `superloopy` isn't found, its folder isn't on your `PATH`; the bootstrap prints the exact line to add. Check everything with `superloopy doctor`.

Installing from a checkout instead? Run `node src/cli.js install --json`.

## Update

If you installed from the Codex marketplace, refresh the marketplace snapshot:

```
codex plugin marketplace upgrade beefiker
```

Superloopy checks for updates on `SessionStart`. Marketplace installs are Codex-managed, so Superloopy never starts an `npx` self-update for them; when a newer version is detected, it tells you to run the marketplace upgrade and re-approve modified hooks.

Restart Codex after the upgrade. If hooks show up as Modified, approve them; the following approved session reruns the `SessionStart` bootstrap on the new version. Then run `superloopy doctor`.

If the plugin still looks stale or degraded after that, do a repair reinstall from the refreshed marketplace:

```
codex plugin add superloopy@beefiker
```

If you installed from a checkout, update the checkout and rerun the installer:

```
git pull --ff-only
node src/cli.js install --json
superloopy doctor
```

Checkout installs are not `npx`-managed. `npx` self-update is reserved for a future installer that writes a `superloopy-install.json` snapshot into a stable install root.

## Troubleshooting

If plugin install or upgrade commands fail, update the Codex CLI first. `codex plugin add` is available in Codex CLI 0.131.0 and newer; older builds can have trouble with current plugin marketplace commands and hook approval flows.

After updating the CLI, restart Codex, run the marketplace install or upgrade command again, approve any Modified hooks, then check with `superloopy doctor`.

## Uninstall

Remove the installed plugin from Codex:

```
codex plugin remove superloopy@beefiker
```

If you no longer need the marketplace source, remove it too:

```
codex plugin marketplace remove beefiker
```

Restart Codex after uninstalling. Optional local bootstrap cleanup: plugin removal handles Codex's plugin config and cache, but the `superloopy` wrapper and copied personal agents can remain. Review before deleting them, especially if you customized any agent file.

```
rm -f ~/.local/bin/superloopy
rm -f ~/.codex/agents/franky.toml ~/.codex/agents/zoro.toml ~/.codex/agents/usopp.toml ~/.codex/agents/jinbe.toml ~/.codex/agents/robin.toml ~/.codex/agents/nami.toml
```

If you installed with `CODEX_HOME`, `SUPERLOOPY_BIN_DIR`, or `CODEX_LOCAL_BIN_DIR`, clean up those configured paths instead.

<sub>MIT licensed.</sub>
