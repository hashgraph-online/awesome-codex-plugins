<div align="center">

# 🌀 Superloopy

**Loop engineering for Codex and Claude Code.** Type `loopy <task>` — an agent does the work, proves each piece with real evidence, and only then says it's done.

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

After installing, type your task in Codex or Claude Code with a leading `loopy`:

```
loopy add the payments module
```

The agent plans it, proves each piece with a real file, and reports back — you don't run any commands yourself. The packaged Stop hook stays quiet unless `SUPERLOOPY_STOP_HOOK=on`.

## Why Superloopy?

Superloopy is for Codex and Claude Code work where "done" needs to mean more than a confident status sentence.

- Evidence-first: every pass points at a real artifact under `.superloopy/evidence/`.
- Lightweight by default: one small CLI, repo-local state, zero runtime dependencies.
- Agent-friendly: skills, hooks, and optional crew lanes guide the agent without hiding the final gate.

**Guarantee scope.** Command-backed criteria are the strong guarantee: at completion Superloopy re-runs each command in-process and requires it to reproduce, so a stale or fabricated pass cannot reach "done". Manual (commandless) criteria are verified as a non-empty evidence artifact plus auditor/human judgment — their correctness rests on review, not the deterministic re-run.

## Skills

Superloopy keeps the command layer small. Skills carry the specialist workflow: when to use it, what the agent should inspect, and what proof must be left under `.superloopy/evidence/`.

| Skill | Use it when | What it produces |
| --- | --- | --- |
| `superloopy-loop` | You type `loopy <task>` or `loopy team <task>` for a full loop; use `loopywork`, `lpy`, or `$lpy` for guidance-only context. | Full loops produce a lightweight plan, guided next actions, command-backed proof, a quality gate, and a final evidence report. Guidance aliases do not mutate state. |
| `superloopy-doctor` | You diagnose install, wrapper, plugin cache, hook/bootstrap, agent, Codex/Claude Code host wiring, or stale-version problems. | A read-only health report with wrapper/cache/version evidence, failing checks, and the exact repair command to run only if approved. |
| `superloopy-research` | You ask for `loopy research`, deep research, exhaustive investigation, or a cited report. | Research axes, expansion waves, a claim ledger, verification notes, and a cited synthesis artifact. |
| `superloopy-clone` | You ask for `loopy clone`, authorized website cloning, rebuilding, migration, or pixel-focused page recovery. | Browser captures, page topology, design tokens, asset inventory, implementation notes, build output, and visual QA evidence. |
| `superloopy-frontend` | You build, style, or redesign any UI/page/component, or ask to make something look designed (auto-activates on visual work). | A DESIGN.md token contract, an anti-slop pre-flight result, and a real-browser visual-QA evidence artifact. |
| `humanize-korean` | Use when Korean users ask to remove AI tone, fix 번역투, or make Korean text sound human without changing facts. | Writes `final.md`, `summary.md`, and `audit.json`; in Superloopy loops it records evidence under `.superloopy/evidence/humanize-korean/`. |
| `superloopy-slides` | You ask for slides, a presentation, a deck, or a PPT/PPTX-to-web conversion. | A zero-dependency single-file HTML deck on a fixed 16:9 stage, three style previews to pick from, and a rendered-screenshot visual-QA artifact under `.superloopy/evidence/slides/`. |

The loop skill is the default guardrail. `loopy` starts or resumes the evidence loop; `loopy team` escalates to crew mode. `loopywork`, `lpy`, and `$lpy` only inject starter guidance. Research and clone are opt-in specialist modes, and both still finish by recording Superloopy evidence instead of trusting a status sentence. The frontend skill auto-activates on visual work and injects a short guidance-only steer; set `SUPERLOOPY_FRONTEND_STEER=off` to silence it.

## Clone Demo

[![Transferloom.com clone reference](.github/assets/transferloom-clone-reference.png)](https://transferloom.com/)

`superloopy-clone` reproduced Transferloom.com locally and passed desktop/mobile browser validation. The reference run preserved the sticky nav, animated hero, app preview sections, comparison table, security panel, sister app banner, footer, local assets, and Superloopy evidence trail.

## Slides Demo

[![Fileloom intro deck built with superloopy-slides](.github/assets/slides-demo-reference.png)](https://fileloom-slides.pages.dev)

`superloopy-slides` generated this **[live multilingual deck →](https://fileloom-slides.pages.dev)** — a zero-dependency single-file HTML presentation on a fixed 16:9 stage in English · 한국어 · 中文 · 日本語 · Español. It passed real-browser visual-QA (standalone, phone letterbox, and iframe embed) recorded under `.superloopy/evidence/slides/`.

## The crew

For bigger work, Superloopy ships six optional subagents — each owns one lane (`.codex/agents/*.toml` on Codex, bundled `agents/*.md` on Claude Code). They come with the plugin (no command needed); on Codex, `superloopy agents install` just re-copies them if you ever need it. Their advisory model defaults are documented in `docs/superloopy-model-policy.md` (Codex) and `docs/superloopy-model-policy-claude.md` (Claude Code), and checked by `superloopy doctor`.

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

## Works with Superpowers

Superloopy sits well next to the [Superpowers](https://github.com/obra/superpowers) plugin. They handle different halves of the same job, so you don't have to choose one.

- Superpowers runs the front of the loop: brainstorming, planning, and its TDD and code-review methodology.
- Superloopy runs the finish: command-backed criteria that re-run at completion, so "done" is proven, not just claimed.

When Superpowers is installed (on Codex or Claude Code), Superloopy notices and steers its own guidance to match. It leaves design, planning, and TDD to Superpowers and keeps itself as the outer evidence gate. Detection is best-effort and only shapes advice; it never weakens a gate. Set `SUPERLOOPY_SUPERPOWERS=off` to opt out or `on` to force it, and run `superloopy doctor` to see what was found. More in [docs/superloopy-interop-superpowers.md](docs/superloopy-interop-superpowers.md).

### Q&A

- **Do I need both?** No. Superloopy works on its own. If Superpowers is there too, the two coordinate instead of overlapping.
- **Which stage does each own?** Superpowers owns brainstorm, plan, and build. Superloopy owns the proof at the end. Keep one driver per task: don't run `loopy team` and the Superpowers subagent flow on the same slices at once.
- **Who decides a task is done?** Superloopy. Its check re-runs the real command at the end and blocks a false pass.
- **How is Superpowers detected?** By looking in your Codex and Claude Code plugin folders. You can always override with `SUPERLOOPY_SUPERPOWERS=on|off`.

## Install

Superloopy installs on both **Codex** and **Claude Code** from one repo. The core (loop state, evidence gates, doctor) is host-agnostic; each host gets its own thin plugin manifest, hook wiring, and agent format.

For agent-driven installs such as `install https://github.com/beefiker/superloopy`, use [installation.md](installation.md). It is written as a host-selection and verification checklist for Codex and Claude Code agents.

### Codex

Needs Node.js ≥ 20 and Codex CLI ≥ 0.131.0 for `codex plugin add`. Superloopy is dependency-free — zero runtime dependencies, just Node.

```
codex plugin marketplace add https://github.com/beefiker/superloopy
codex plugin add superloopy@beefiker
```

Restart Codex after installing the plugin. If Codex asks you to review hooks, approve them; the next approved session runs a `SessionStart` hook that does a one-time bootstrap — it installs the `superloopy` command and the agents. If `superloopy` isn't found, its folder isn't on your `PATH`; the bootstrap prints the exact line to add. Check everything with `superloopy doctor`.

Installing from a checkout instead? Run `node src/cli.js install --json`.

### Claude Code

Needs Node.js ≥ 20. From the same repo:

```
/plugin marketplace add beefiker/superloopy
/plugin install superloopy@beefiker
```

Reload plugins (or restart Claude Code) and approve the hooks when prompted. On Claude Code the skills, subagents (`agents/*.md`), and hooks (`hooks/hooks.json`) are **plugin-bundled** — there is no `~/.codex` install step and no `superloopy` wrapper; the hooks invoke the CLI directly via `${CLAUDE_PLUGIN_ROOT}`, and `SessionStart` is a clean no-op (nothing to bootstrap). For local development, point Claude Code at a checkout with `claude --plugin-dir <checkout>`. Verify with `node "${CLAUDE_PLUGIN_ROOT}/src/cli.js" doctor --json`. The subagents' advisory model defaults for Claude are documented in `docs/superloopy-model-policy-claude.md`.

## Update

### Codex

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

### Claude Code

Refresh the marketplace, reinstall to resolve the new version, then reload — no restart needed:

```
/plugin marketplace update beefiker
/plugin install superloopy@beefiker
/reload-plugins
```

There is no separate `/plugin update` command: reinstalling from the refreshed marketplace resolves the new version, and `/reload-plugins` applies it in the current session (no Claude Code restart, and hooks do not need re-approval). Verify with `node "${CLAUDE_PLUGIN_ROOT}/src/cli.js" doctor --json`. If you loaded a checkout with `--plugin-dir`, just `git pull --ff-only` and run `/reload-plugins`.

## Troubleshooting

If plugin install or upgrade commands fail, update the Codex CLI first. `codex plugin add` is available in Codex CLI 0.131.0 and newer; older builds can have trouble with current plugin marketplace commands and hook approval flows.

After updating the CLI, restart Codex, run the marketplace install or upgrade command again, approve any Modified hooks, then check with `superloopy doctor`.

On Claude Code, if `/plugin` commands fail or the plugin looks stale, run `/reload-plugins` (or restart Claude Code) and verify with `node "${CLAUDE_PLUGIN_ROOT}/src/cli.js" doctor --json`.

## Uninstall

### Codex

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
Remove-Item "$env:APPDATA\npm\superloopy.cmd" -ErrorAction SilentlyContinue
rm -f ~/.codex/agents/franky.toml ~/.codex/agents/zoro.toml ~/.codex/agents/usopp.toml ~/.codex/agents/jinbe.toml ~/.codex/agents/robin.toml ~/.codex/agents/nami.toml
```

If you installed with `CODEX_HOME`, `SUPERLOOPY_BIN_DIR`, or `CODEX_LOCAL_BIN_DIR`, clean up those configured paths instead.

### Claude Code

```
/plugin uninstall superloopy@beefiker
/plugin marketplace remove beefiker
```

Then run `/reload-plugins`. Nothing else to clean up — Claude Code installs are fully plugin-bundled (no `superloopy` wrapper, no `~/.codex` writes). Removing the marketplace from its last remaining scope also uninstalls the plugin.

<sub>MIT licensed.</sub>
