<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.png">
  <img alt="Figma Maxxing. Agent skills for real Figma files, by Thiago Xikota. A fill shown twice: raw hex #DC000C struck through, then the token color/brand/signal. 8 skills, 90 gotchas." src="assets/banner-light.png">
</picture>

# figma-maxxing

**I wrote 8 Agent Skills for agents that edit real Figma files.**

Most rules came from something that broke in a real file. They tell your agent what to inspect before editing and how to check the result.

**[Install and try it](#quick-start)** · [Your agent's setup](#install-for-your-agent) · [Leia em português](docs/README.pt-BR.md)

90 gotchas · a handoff gate with 17 checks

[![Test](https://github.com/thiagoxikota/figma-maxxing/actions/workflows/test.yml/badge.svg)](https://github.com/thiagoxikota/figma-maxxing/actions/workflows/test.yml)
[![skills.sh](https://www.skills.sh/b/thiagoxikota/figma-maxxing)](https://www.skills.sh/thiagoxikota/figma-maxxing)
[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)

## Quick start

Install the skills:

```bash
npx skills add thiagoxikota/figma-maxxing
```

Connect your agent to Figma through Figma's official MCP server or figma-console-mcp ([setup](#what-you-need)). Then paste a frame link and ask: "Run figma-slop-check and figma-handoff-gate on this frame. Report what needs fixing."

You need a coding agent that loads skills and Node.js for `npx`. Installation ran in Claude Code, Codex, Copilot CLI and Gemini CLI. Cursor and the Claude desktop and web apps were not tested. Without a coding agent, [use this prompt](#paste-this-into-your-ai) to ask for checks you can do yourself.

## Before and after

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/demo/before-after-dark.png">
  <img alt="The same Team members screen before and after the checks. Markers 1 to 8 on the before screen point at the layers named in the list below. figma-slop-check found 16 issues before (4 critical, 6 high, 4 medium, 2 low) and 6 after the fix pass (1 critical, 2 medium, 3 low)." src="assets/demo/before-after-light.png">
</picture>

**Test on Figma's official MCP server, 2026-10-05: 10 of 10 planted defects found, 0 missed.** The agent that planted the defects had read the skills, the auditor's prompt said where to look, and this was one screen in one run.

One agent built a demo screen with 10 planted defects and an answer key. A second agent, without the key, ran `figma-slop-check` and `figma-handoff-gate`. A third compared the audit with the key. The audit also flagged 14 items outside the key (13 distinct problems: both gates flagged the same rename). After one fix pass, `figma-slop-check` went from 16 findings to 6, but neither gate passed. There is also a [9-second animation](assets/demo/demo.gif).

<details>
<summary>The markers, how the test ran, and its limits</summary>

The markers point at the first 8 items of the `figma-slop-check` punch list, in the run's own words:

1. **WCAG:** upsell card body below the contrast and size floor
2. **NAMING:** default Figma name on the upsell card
3. **NAMING:** default Figma name on a divider
4. **NAMING:** default Figma names on the meta icon
5. **INSTANCE:** detached copy of ListItem
6. **TOKEN:** title raw hex
7. **ICON:** hand-drawn person icon instead of Icon/User
8. **RADIUS:** summary card radius off the scale

The test used a demo screen with 10 planted defects and an answer key. The agent that built it had read the skills. A second agent, who never saw the key, ran `figma-slop-check` and `figma-handoff-gate` through Figma's official MCP server. Its prompt told it what to inspect: bound variables, instances versus frames, spacing, radius, names and text bounds. A third agent, the judge, compared the punch list with the key.

**10 of 10 planted defects found, 0 partial, 0 missed.** The agent that planted the defects had read the skills, the auditor's prompt said where to look, and this was one screen in one run. The punch list had 27 items: 16 from `figma-slop-check` and 11 from `figma-handoff-gate`. Of those, 13 match a planted defect (some defects show up in more than one item). The other 14 items point at problems outside the key: 13 distinct ones, because both gates flagged the same rename. None contradicted the key or the screenshots, though 2 could not be checked without opening the file, and the judge did not open it. One of the 14 is a contrast failure the answer key itself missed.

Then a fourth agent ran `figma-preflight`, fixed the screen and read back every property it changed. Both checks ran again, and neither passes yet:

- **figma-slop-check:** 16 findings down to 6, 1 of them critical (no focus state anywhere). Of the 6 left, 2 carry over from the first audit, 2 were already on the screen but the first audit did not report them, and 2 came from the fix itself.
- **figma-handoff-gate:** 11 issues up to 13 (8 blockers), mostly flows and states the fix pass did not draw.

Real screenshots from the official Figma MCP, 2026-10-05, on a demo file built for the test. The agent that planted the defects had read these skills, and the auditor's prompt pointed at the properties where most of them sat. So the test shows that the checks fire on a live Figma file built for the test, not that they catch everything. [works-with.md](docs/works-with.md#blind-demo-on-the-official-figma-mcp) lists the tool calls and what the official server could not do.

</details>

## Paste this into your AI

No install needed. Copy this into your AI and fill in the brackets. The prompt ran in the Claude, Codex and Gemini terminal tools. Chat apps were not tested.

```text
Read and use this file as reference:
https://raw.githubusercontent.com/thiagoxikota/figma-maxxing/main/llms.txt
If you cannot open it, tell me and do
not guess.
I am a designer. I [do / do not] have
an AI agent connected to Figma.
My context: [Figma plan, whether my
files have a design system, solo or
team].
Pick at most five rules for my work.
For each one, give me one check I can
do in Figma today. Then tell me
whether any skill is worth installing
for me.
```

## What goes wrong, and what catches it

- The agent draws an icon your library already has → `figma-preflight` searches first.
- "Done," says the agent, and nothing changed → read-back rules in `figma-preflight`.
- Raw hex, default layer names, a detached row → `figma-slop-check`.
- The handoff shows "add" and never "remove" → `figma-handoff-gate`.
- You work through the comments one by one, by hand → `figma-comment-fix-loop`.
- The bridge dropped again → `figma-bridge-doctor`.

## The skills

- **[`figma-canon`](skills/figma-canon/SKILL.md)** · The rules and the gotchas. Loaded piece by piece, only what the task needs.
- **[`figma-preflight`](skills/figma-preflight/SKILL.md)** · Before every write. Tells the agent to run the checks and return a verdict or a fix list, without changing the canvas.
- **[`figma-orient`](skills/figma-orient/SKILL.md)** · First contact with a file. Maps pages, components and variables, and saves the map.
- **[`figma-slop-check`](skills/figma-slop-check/SKILL.md)** · After a write. Tells the agent to review generated copy, layout and values that drift off your scales and tokens.
- **[`figma-handoff-gate`](skills/figma-handoff-gate/SKILL.md)** · Before a handoff. Every action needs a destination and a way back.
- **[`figma-comment-fix-loop`](skills/figma-comment-fix-loop/SKILL.md)** · When feedback arrives. Turns open comments into fixes, with evidence for each one.
- **[`figma-click-flow`](skills/figma-click-flow/SKILL.md)** · "Turn this into a flow." Draws arrows from tappable elements to their screens.
- **[`figma-bridge-doctor`](skills/figma-bridge-doctor/SKILL.md)** · The figma-console bridge dropped. Diagnoses and repairs it (macOS scripts).

<details>
<summary>How they fit together</summary>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/flow-dark.png">
  <img alt="How the skills fit together: 01 map the file with figma-orient, 02 check before writing with figma-preflight, 03 write with use_figma or figma_execute, 04 check after writing with figma-slop-check, 05 hand off with figma-handoff-gate. figma-canon holds the rules every step reads; figma-comment-fix-loop runs steps 02 to 04 once per comment." src="assets/flow-light.png">
</picture>

</details>

## A few gotchas

- [Changing `action` on a prototype reaction does nothing.](skills/figma-canon/references/field-notes.md#re-pointing-a-reaction-write-actions-not-action) Figma reads `actions`, and the call still returns success.
- [`instance.resize()` leaves the icon at full size inside a small box.](skills/figma-canon/references/plugin-api-anomalies.md#instanceresize-does-not-scale-the-children-use-rescale) Use `rescale()`.
- [New sections come out black, though their fill is bound to a color variable.](skills/figma-canon/references/field-notes.md#a-section-fill-bound-to-a-variable-renders-the-base-color-you-passed) A section renders the base color you passed when binding, not the variable. Resolve the variable first, then bind.
- [In one sweep through the figma-console bridge, writes under a locked group did not take.](skills/figma-canon/references/field-notes.md#writes-under-a-locked-ancestor-did-not-take-through-the-figma-console-bridge) Nothing threw, and each layer read `locked: false`. Figma's typings say `locked` does not block plugin writes, so the cause is not established. A count after the sweep is what caught it.

**[Every gotcha, indexed by symptom](docs/gotchas.md)**, in the words a designer would use, plus a list [by error message](docs/gotchas.md#by-error-message).

## Why this, if Figma has official skills

Figma's own skills help an agent create things in Figma. The skills here check the agent's work before and after each write, and again at handoff. Use both. [landscape.md](docs/landscape.md#how-figma-maxxing-composes-with-figmas-skills) maps the servers and skill sets around Figma, with dates.

- **figma-console bridge:** all 8 skills, in my own production work.
- **Official Figma MCP:** `figma-preflight`, `figma-slop-check` and `figma-handoff-gate` ran there once, on the demo file of the test above, with some steps adapted or skipped ([the list](docs/works-with.md#blind-demo-on-the-official-figma-mcp)). That run used the earlier rigor lens of `figma-slop-check`; 1.2.0 rewrote it as 11 rigor checks in 5 groups. `figma-orient`, `figma-comment-fix-loop` and `figma-click-flow` describe that path and have not run on it yet. `figma-bridge-doctor` does not apply.

Skill by skill: [works-with.md](docs/works-with.md).

## Install for your agent

`npx skills add thiagoxikota/figma-maxxing` covers most agents. The skills CLI is a third-party tool that sends anonymous install counts; `DISABLE_TELEMETRY=1` turns that off.

Every route below except Cursor's ran on 2026-10-05 in a clean test folder, and each one installed the 8 skills at version 1.1.1. Claude Code, Codex, Copilot CLI and `npx skills add thiagoxikota/figma-maxxing` installed from GitHub main at commit 3693845, the commit tagged v1.1.1; Claude Code ran through the `claude plugin` CLI, the terminal form of the two slash commands. Gemini CLI installed the v1.1.1 release. `-a opencode` and `-a windsurf` ran earlier the same day from a local copy of the repository.

<details>
<summary><b>Claude Code</b></summary>

```text
/plugin marketplace add thiagoxikota/figma-maxxing
/plugin install figma-maxxing@figma-maxxing-skills
```

Skills show up as `/figma-maxxing:figma-preflight` and so on. The plugin ships skills only: no hooks, no MCP server. The skill descriptions cost about 1,200 tokens in every session (`claude plugin details`, Claude Code 2.1.289).

</details>

<details>
<summary><b>Codex</b></summary>

```bash
codex plugin marketplace add thiagoxikota/figma-maxxing
codex plugin add figma-maxxing@figma-maxxing-skills
```

Ran with codex-cli 0.156.1.

</details>

<details>
<summary><b>GitHub Copilot CLI</b></summary>

```bash
copilot plugin marketplace add thiagoxikota/figma-maxxing
copilot plugin install figma-maxxing@figma-maxxing-skills
```

Ran with Copilot CLI 1.0.61.

</details>

<details>
<summary><b>Gemini CLI</b></summary>

```bash
gemini extensions install https://github.com/thiagoxikota/figma-maxxing
```

Ran with Gemini CLI 0.43.0, which installed 1.1.1 from the latest GitHub release. It asks you to trust the folder and to confirm the install; `--consent` answers both, which is how the test ran.

</details>

<details>
<summary><b>Cursor</b> (not tested)</summary>

I do not have Cursor installed, so this route has not run. According to its docs, Cursor reads `.cursor-plugin/plugin.json`. To try it, copy the repository to `~/.cursor/plugins/local/figma-maxxing` and reload the window. Or use the skills CLI:

```bash
npx skills add thiagoxikota/figma-maxxing -a cursor
```

</details>

<details>
<summary><b>OpenCode, Windsurf and other agents</b></summary>

```bash
npx skills add thiagoxikota/figma-maxxing -a opencode
npx skills add thiagoxikota/figma-maxxing -a windsurf
```

`-a` also takes `codex`, `cursor`, `gemini-cli`, `github-copilot` and `claude-code`. Add `-g` to install in your home folder. In a test, the CLI wrote the 8 skills to `.agents/skills` (`.windsurf/skills` for Windsurf, `.claude/skills` for `claude-code`). The agents themselves were not run.

</details>

<details>
<summary><b>Manual copy</b></summary>

```bash
git clone https://github.com/thiagoxikota/figma-maxxing.git
cd figma-maxxing
python3 install.py --scope user --dry-run
```

`--dry-run` shows what would be copied. Then run one of these two lines, not both:

- `python3 install.py --scope user` installs for Claude Code in `~/.claude/skills`.
- `python3 install.py --target agents --scope user` installs in `~/.agents/skills`, for Codex, Cursor, Gemini CLI and others.

The installer copies folders and refuses to overwrite a skill that already exists.

</details>

## What you need

The skills need an agent that loads Agent Skills and a connection to Figma. There are two ways to connect.

**Figma's official MCP server.** Connect with your Figma account through OAuth. In Claude Code:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

For other agents, see [Figma's guide](https://github.com/figma/mcp-server-guide). Writes through `use_figma` need a Full seat, except in your own drafts, where Figma's [MCP server FAQ](https://help.figma.com/hc/en-us/articles/39252411778583-Figma-MCP-server-FAQs) also lets a Dev seat write. On a Starter plan the call budget is small ([field note](skills/figma-canon/references/field-notes.md#the-official-figma-mcp-server-has-a-hard-tool-call-cap-on-a-starter-plan)). Using it means agreeing to the [Figma Developer Terms](https://www.figma.com/legal/developer-terms/).

**[figma-console-mcp](https://github.com/southleft/figma-console-mcp)** by Southleft (MIT). The route I use in my own work, and the one these skills were built on. It runs on your machine and reaches Figma Desktop (macOS or Windows) through its Desktop Bridge plugin. You need Node.js 18 or newer and a Figma personal access token. Last checked against v1.40.8. In Claude Code:

```bash
claude mcp add figma-console -s user \
  -e FIGMA_ACCESS_TOKEN=figd_YOUR_TOKEN_HERE \
  -e ENABLE_MCP_APPS=true \
  -- npx -y figma-console-mcp@latest
```

1. Restart Claude Code. The first start creates the plugin manifest.
2. In Figma Desktop, open a file and go to Plugins, Development, Import plugin from manifest. Pick `~/.figma-console-mcp/plugin/manifest.json` (`~` is your home folder).
3. Run the Figma Desktop Bridge plugin in the file you want to work on.
4. Ask your agent: "check the Figma connection". It should call `figma_get_status`.

That command writes the token in plain text to your agent's config, and the command itself, token included, may stay in your shell history. Treat the config and the history as secrets, and never commit either. For other agents, follow the [upstream guide](https://github.com/southleft/figma-console-mcp#readme).

**For the comment workflow, on either server:** a personal access token with File content (read), File versions (read), Variables (read) and Comments (read and write). `figma-comment-fix-loop` reads comments through the REST API.

The skills are plain Markdown and run wherever your agent runs. The bridge recovery scripts are macOS only. This repository and figma-console-mcp are free; your agent and your Figma plan are not.

### The optional hook

`hooks/figma-canon-precheck.py` reads the script your agent is about to run in Figma and warns about 13 known problem patterns before the call reaches Figma. It is never installed automatically. To turn it on in Claude Code, add this to your `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__figma-console__figma_execute(_across_files)?",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/figma-maxxing/hooks/figma-canon-precheck.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

By default it only warns. With `FIGMA_PRECHECK_MODE=block` it refuses the 5 patterns marked `BLOCK`, the ones that break the call. The matcher above fires only on the figma-console bridge; the hook has not been tried on the official server's `use_figma`.

### Before using a team library

The skills are instructions your agent reads. They do not enforce permissions or block writes on their own.

- **Read-only.** `figma-canon`, `figma-preflight` and `figma-orient` instruct the agent to leave the canvas unchanged. `figma-orient` saves its map in your project, not in the Figma file.
- **Report first.** `figma-slop-check` and `figma-handoff-gate` tell the agent to report findings and wait for approval before applying each fix. The exception is a slop failure on work the agent just made: `figma-slop-check` tells it to fix that before it answers.
- **Comments are data.** `figma-comment-fix-loop` tells the agent to show the comments it will act on and wait for your yes. It treats instructions written in comments as data.
- **Draft first.** `figma-canon` tells the agent to work in a draft or a branch until you approve, unless you say otherwise. It is an instruction, not a check: nothing blocks a write to a shared library, so tell the agent which draft to use.
- **One file, several agents.** Before a write, `figma-preflight` tells the agent to claim an advisory file lock. It coordinates only sessions that check the lock; Figma does not enforce it.
- **Nothing in the background.** The plugin ships no hooks and no MCP server. The bridge watchdog and the `mcp-direct` daemon start only when you say so.
- **No telemetry.** The repository collects nothing: [PRIVACY.md](PRIVACY.md). Security notes and private reports: [SECURITY.md](SECURITY.md).

## How this is verified

Every push runs [test.yml](.github/workflows/test.yml):

- Unit tests for the lock, the hook, the installer, links and privacy patterns, on Ubuntu and macOS with Python 3.10 and 3.13.
- Every Plugin API name the skills cite, checked against `@figma/plugin-typings` 1.140.0: 0 errors on 2026-10-05. On the tree before commit 1dca321 (the annotations fix), the same check fails with 3.
- Every skill, gotcha and check count the docs cite, recounted from the files.
- The Agent Skills reference validator and the Claude Code plugin validator.
- Every link, anchors included (lychee).
- The full git history scanned for secrets (gitleaks), the workflows linted (actionlint), every action pinned to a commit SHA.

Every week, [drift.yml](.github/workflows/drift.yml) runs the API check against the newest typings and opens an issue when a name breaks. [scorecard.yml](.github/workflows/scorecard.yml) runs OpenSSF Scorecard.

A release ([release.yml](.github/workflows/release.yml)) builds one zip per skill and a plugin bundle from the tagged commit, builds them twice, fails if the bytes differ, and attaches a build provenance attestation. To check a download:

```bash
gh attestation verify figma-preflight-1.1.1.zip \
  --repo thiagoxikota/figma-maxxing
```

This repository has an entry in the [M8ven Trust Index](https://m8ven.ai/mcp/thiagoxikota/figma-maxxing), claimed by the author himself. Its public grade is C (Emerging). The code sub-score was 100 out of 100, read on 2026-10-04 at commit 1dca321, before 1.1.0.

[![M8ven Score](https://m8ven.ai/badge/mcp/thiagoxikota-figma-maxxing-1lm8zs?v=4cd8b7012dc0756bb5aa91e8c02089c4)](https://m8ven.ai/mcp/thiagoxikota-figma-maxxing-1lm8zs?s=readme)

## How far this has been tested

As of 2026-10-05:

- **My own work.** I built these skills in Claude Code on macOS with figma-console-mcp, on real files. This public edition is a rewrite of that set: in English, generalized, with every client detail removed. It has not yet run end to end on a second machine.
- **Official Figma MCP.** The test above, on one demo screen. The audit took 12 Figma MCP calls, the fix pass 13, the second audit 13. Some steps had no tool or hit a limit there: no selection, no screenshot above 1x through `get_screenshot`, no bridge status, and a 20 KB cap on each call. The agents used read-only `use_figma` workarounds and logged each one in [works-with.md](docs/works-with.md#blind-demo-on-the-official-figma-mcp).
- **Installs.** Every route in [Install for your agent](#install-for-your-agent) except Cursor, from GitHub main, the v1.1.1 release or a local copy, as listed there.

If something still depends on my setup, [open an issue](https://github.com/thiagoxikota/figma-maxxing/issues) with your environment and the exact error.

## Contributing

A gotcha you hit yourself, with the symptom, cause and fix you ran, belongs here. Questions and before/after shots go to [Discussions](https://github.com/thiagoxikota/figma-maxxing/discussions); bugs and gotchas to [issues](https://github.com/thiagoxikota/figma-maxxing/issues/new/choose). See [CONTRIBUTING.md](CONTRIBUTING.md), the [code of conduct](CODE_OF_CONDUCT.md) and the [changelog](CHANGELOG.md). Working with an agent? Point it at [AGENTS.md](AGENTS.md).

## Who made this

I'm Thiago Xikota, AI Product Designer, founder of Xikota Design and researcher at Lemme (UFSC). I'm writing *Design na era da IA* (Casa do Código, in production). [Follow me on LinkedIn](https://www.linkedin.com/in/thiagoxikota).

## Credits

Built on [figma-console-mcp](https://github.com/southleft/figma-console-mcp) by Southleft. The skill format is the open [Agent Skills](https://agentskills.io) standard.

Not affiliated with Figma. Figma is a trademark of Figma, Inc.

## License

MIT. See [LICENSE](LICENSE).
