# pro-launch

English | [简体中文](https://github.com/jack-reson8/pro-launch/blob/main/README.zh-CN.md) | [日本語](https://github.com/jack-reson8/pro-launch/blob/main/README.ja.md) | [한국어](https://github.com/jack-reson8/pro-launch/blob/main/README.ko.md) | [Tiếng Việt](https://github.com/jack-reson8/pro-launch/blob/main/README.vi.md) | [हिन्दी](https://github.com/jack-reson8/pro-launch/blob/main/README.hi.md)

A Claude Code skill that takes a product from 0 to 1 **taste-first**: positioning → naming, domains & trademark → reference hunting (GitHub/open-source first, then App Store and award winners) → style bible → feature map → UI/UX build loop → asset generation → device QA → launch video → GTM → growth → open-source / App Store shipping.

Why it exists: most AI-built products fail not on code but because (1) no real references were studied, (2) the model grades its own work, (3) the user's repeated corrections never get written down. Every phase here forces a **real artifact** and a **gate** (`scripts/phase_gate.py`) before the next phase starts.

## Install

In Claude Code:

```
/plugin marketplace add jack-reson8/pro-launch
/plugin install pro-launch@pro-launch
```

Or as a plain skill folder:

```bash
git clone https://github.com/jack-reson8/pro-launch /tmp/pro-launch && cp -R /tmp/pro-launch/plugins/pro-launch/skills/pro-launch ~/.claude/skills/
```
Then ask Claude Code things like "build me an app", "this UI looks generic", "find references", "name this product", "plan the launch".

**Codex** (CLI or the ChatGPT desktop app):

```bash
codex plugin marketplace add jack-reson8/pro-launch
codex plugin add pro-launch@pro-launch
```

Or copy `plugins/pro-launch/skills/pro-launch` into `~/.codex/skills/`. The skill follows the open [Agent Skills](https://agentskills.io) standard, so it works in Claude Code, Codex and any agent that reads SKILL.md.

**Other agents** (Cursor, Gemini CLI, GitHub Copilot and other agents supported by the skills CLI):

```bash
npx skills add jack-reson8/pro-launch
```

## What's inside

The skill lives in `plugins/pro-launch/skills/pro-launch`; all paths below are relative to that folder.

- `SKILL.md` – phases, gates, iron rules
- `references/01-13` – one page per phase (incl. trademark & IP for multi-country launches)
- `references/mistakes.md`, `user-repeated-demands.md` – ledger of real mistakes and the demands users repeat
- `scripts/` – phase gate, App Store poster downloader, reference archiver, domain/App Store name check, cutout→vector pipeline (Vision + vtracer + svgo)
- `examples/`, `assets/` – worked examples and templates

MIT licensed. Works with Claude Code skills; the method is portable to other agents.
