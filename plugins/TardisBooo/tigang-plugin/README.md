<div align="center">

<img src="docs/logo.svg" width="160" alt="tigang-reminder logo" />

# tigang-reminder

**Take a Kegel break after your agent runs a successful `git commit` or `git push`.**

A movement reminder for people who code with agents.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Node >= 18](https://img.shields.io/badge/node-%3E%3D18-green.svg)
![Zero dependency](https://img.shields.io/badge/dependency-0-blue.svg)
![Zero token](https://img.shields.io/badge/token-0-brightgreen.svg)

**Claude Code** · **Codex CLI** · **pi** · **dsh** — four agents, one shared set of stats

**English** · [简体中文](README.zh-CN.md)

</div>

---

## Why

A successful commit or push can be a cue to pause during a long coding session. Tigang displays an optional Kegel break reminder when the agent finishes its turn.

The host's hook detects the Git operation and displays the reminder.

## How it works: the reminder lands at the end of the AI's answer — zero tokens

```
agent runs Bash: git commit / git push
        │
        ▼
detection (PostToolUse / tool_result)          ← core.detect(command, output)
        ├─ regex-matches git commit / git push (handles git -C path commit,
        │  cd x && git push, commit && push, …; quoted strings are stripped
        │  first, so "text that mentions git push" never false-positives)
        ├─ nothing to commit / push rejected / fatal → not counted
        ├─ counters appended to ~/.claude/tigang-reminder/stats.json
        ├─ reminder stashed in pending.json (merged within a turn, 30-min TTL)
        └─ zero stdout → never enters model context → zero token cost
        │
        ▼  ……the agent keeps working and finishes its answer……
        │
turn end (Stop / agent_settled / turn end)     ← core.takePendingMessage()
        └─ the terminal renders the reminder at the end of the AI's answer
           (systemMessage / ui.notify / ANSI tty — bypasses the model, zero tokens)
```

Letting the model "say" the reminder feels natural, but every commit injects context + generates text — a steady token burn. A display-layer append **looks** like part of the AI's answer while bypassing the model entirely.

### Zero context pollution — by design

| Phase | What it does | Enters model context? |
| --- | --- | --- |
| Detection (PostToolUse / tool_result) | reads the tool payload, writes local JSON — produces **zero stdout** | nothing |
| Reminder (turn end) | `systemMessage` / `ui.notify` / ANSI tty — display-layer rendering only | nothing |
| Any failure | silent `exit 0`, never blocks git or the session | nothing |

The two channels that *could* reach the model — hook stdout, and a Stop hook's `decision: "block"` reason — are deliberately unused. The only context footprint is the static one-line description of the `/tigang-stats` command; its body loads only when you invoke it.

## Install

### Too lazy to copy commands? Throw the link at your agent

Paste this into whatever agent you're already talking to — Claude Code, Codex CLI, pi, dsh. It reads this README and picks the right path for itself:

```text
Install the tigang-reminder plugin from https://github.com/TardisBooo/tigang-plugin.
Follow the README's install instructions for the agent you are, then tell me how to verify it works.
```

### Claude Code (native plugin)

```bash
claude plugin marketplace add TardisBooo/tigang-plugin
claude plugin install tigang-reminder@tigang
```

Already-running sessions: run `/reload-plugins --force` once to activate — no restart needed.

### Codex CLI

```bash
codex plugin marketplace add TardisBooo/tigang-plugin
codex plugin add tigang-reminder@tigang
```

Open `/hooks` in an interactive session to review and trust the two hooks.
See the [Codex adapter](adapters/codex/README.md) for migration from manual hooks.

### pi (@earendil-works/pi-coding-agent)

```bash
cp adapters/pi/tigang-reminder.ts ~/.pi/agent/extensions/
cp hooks/tigang_core.js ~/.pi/agent/extensions/
```

See **[adapters/pi/README.md](adapters/pi/README.md)**.

### DSH headless (DeepSeek Harness)

```bash
dsh plugin --profile headless add github:TardisBooo/tigang-plugin
```

On DSH 0.2.2-rc.1, the native bundle writes one reminder per turn to stderr after
successful Git commits or pushes. The `--json` event stream stays on stdout.
See the [DSH adapter guide](adapters/dsh/README.md) for setup and removal.

> Which files each install path touches, and how to uninstall: see **[INSTALL.md](INSTALL.md)**.

## Usage

- Just let your agent commit and push — nothing else to do.
- View stats: run `/tigang-reminder:tigang-stats` in a Claude Code session, or read
  `~/.claude/tigang-reminder/stats.json` directly.
- All four agents share one set of stats (today / total / commits vs pushes).
- Reminder language follows your system locale: **English / 简体中文 / 繁體中文 / 日本語 / 한국어 / Español**;
  force one with `TIGANG_LANG` (e.g. `TIGANG_LANG=en`). Uncovered languages fall back to English.
- For testing or isolation: point `TIGANG_STATE_DIR` at another directory.

## False-positive protection

- Commands are split on `&&`, `||`, `;`, `|` and newlines; each segment must match `git [global-options] commit|push`
- Quoted strings are stripped before matching — `git commit -m "mentions push"` never counts
- Outputs like `nothing to commit`, `! [rejected]`, `fatal:` are treated as no-ops
- Failed commands (non-zero exit code / `isError`) never count

## FAQ

**Does it cost tokens?** No. Detection produces zero output; the reminder is rendered by the terminal's display layer at turn end. The model never sees it.

**Privacy?** Zero network requests. Everything stays in two local JSON files under `~/.claude/tigang-reminder/`.

**Multiple sessions or agents?** Each installed adapter uses the same local stats and pending reminder files by default.

**I want reminders on my own manual commits too?** Give git a global post-commit template hook:

```bash
git config --global init.templatedir ~/.git-template
mkdir -p ~/.git-template/hooks
printf '#!/bin/sh\necho "💪 [Kegel break] Another commit! Squeeze 3s → release 3s, 10 reps"\n' > ~/.git-template/hooks/post-commit
chmod +x ~/.git-template/hooks/post-commit
```

(Only affects repos cloned/init'ed afterwards; copy the hook into existing repos manually.)

## Repository layout

```
tigang-plugin/
├── .claude-plugin/
│   ├── plugin.json          # Claude Code plugin manifest
│   └── marketplace.json     # marketplace (single-plugin repo, source: "./")
├── .agents/plugins/          # Codex marketplace
├── .codex-plugin/            # Codex plugin manifest
├── core/                     # compatibility path for existing adapters
├── hooks/
│   ├── hooks.json           # Claude Code hook configuration
│   ├── codex-hooks.json     # Codex hook configuration
│   ├── tigang_core.js       # shared detection, stats and reminder text
│   └── tigang_hook.js       # entry script (detect / remind modes)
├── adapters/
│   ├── codex/README.md      # Codex installation and migration
│   ├── dsh/                 # DSH headless bundle and manual adapter
│   └── pi/tigang-reminder.ts# pi extension: tool_result detect + agent_settled render
├── commands/
│   └── tigang-stats.md      # /tigang-stats — view your stats
├── tests/
│   └── test_core.js         # npm test
└── docs/
    └── logo.svg             # logo (cat butt × starburst)
```

## Contributing & License

- Guide for adding a new agent adapter: [CONTRIBUTING.md](CONTRIBUTING.md) — the core pattern is just two functions.
- Unit tests: `npm test` (zero dependencies, < 5 s).
- [CHANGELOG.md](CHANGELOG.md) · [SECURITY.md](SECURITY.md) · [INSTALL.md](INSTALL.md)
- MIT License © 2026 TardisBooo

---

<div align="center">

**Your set starts now: squeeze 3 s → release 3 s, 10 reps — keep breathing.** 💪

</div>
