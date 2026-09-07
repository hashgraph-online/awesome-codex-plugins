# Computer Usage Summary Skill

[![CI](https://github.com/liuyewang/computer-usage-summary-skill/actions/workflows/test.yml/badge.svg)](https://github.com/liuyewang/computer-usage-summary-skill/actions/workflows/test.yml)
[![skills.sh](https://skills.sh/b/liuyewang/computer-usage-summary-skill)](https://skills.sh/liuyewang/computer-usage-summary-skill)
[![License: MIT](https://img.shields.io/badge/License-MIT-0f766e.svg)](LICENSE)
[![Local first](https://img.shields.io/badge/privacy-local--first-0f766e.svg)](PRIVACY.md)

**See where your time went, without sending it anywhere.**

A privacy-first Codex skill-only plugin that turns local
[ActivityWatch](https://activitywatch.net/) data into copyable daily overview,
app usage, local-time timeline, and foreground browser-page tables. The current
workflow targets macOS and keeps all activity data on the machine.

中文简介：这是一个基于本机 ActivityWatch 的 macOS 电脑使用情况汇总技能。它不会
上传活动数据，不安装浏览器扩展，也不会展示完整网址。

## Requirements

- macOS
- Python 3.9 or newer
- ActivityWatch running locally with the window and AFK watchers enabled

Install ActivityWatch from an official source of your choice. Before enabling
automatic startup, verify its publisher and operating-system security prompt.
On macOS, verify its code signature and Gatekeeper status. This
repository never downloads, installs, or starts ActivityWatch automatically.

## Install In Codex

Install the repository as a skill-only Codex plugin, or install the
`skills/computer-usage-summary` directory directly with Codex's skill
installer.
For a local clone under active development, link the source directory so every
source edit is used directly without reinstalling:

```bash
ln -s /absolute/path/to/computer-usage-summary-skill/skills/computer-usage-summary \
  ~/.codex/skills/computer-usage-summary
```

Start a new Codex task after creating or replacing the link so skill metadata
is rediscovered.

After this repository is published, a GitHub-directory install looks like:

```text
$skill-installer install https://github.com/liuyewang/computer-usage-summary-skill/tree/main/skills/computer-usage-summary
```

## Usage

Ask Codex: `Summarize what I did today on my Mac.`

Or run the bundled script directly:

```bash
# Complete copyable Markdown report
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today

# Paste an application table into Excel, Numbers, or Feishu Sheets
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --format tsv --table apps

# Multi-day report using inclusive local dates
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --start 2026-07-20 --end 2026-07-26

# Structured JSON for additional analysis
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --format json

# Paste a chronological timeline into a spreadsheet
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --format markdown --table timeline

# Show foreground browser pages with at least two minutes of active time
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --table browser --min-tab-seconds 120

# Save a UTF-8 CSV application table
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --format csv --table apps --output daily-apps.csv
```

Tables are available as `summary`, `daily`, `apps`, `browser`, and `timeline`.
The default `report` combines the daily, app, browser, and timeline tables.
User-facing times use the Mac system timezone unless an explicit
`--timezone Area/City` override is supplied.

See the [local-first landing page](https://liuyewang.github.io/computer-usage-summary-skill/)
for a synthetic report preview and the [design-partner guide](docs/DESIGN_PARTNERS.md)
to help shape future reports without sharing activity data.

## Limitations

Accurate historical foreground and AFK time begins only after ActivityWatch
starts recording. Browser rows contain only pages observed in the foreground;
they do not represent every open tab or browser history. Without ActivityWatch,
macOS has no reliable public history for foreground-app time or launches.

See [PRIVACY.md](PRIVACY.md) for the data-handling rules and
[CONTRIBUTING.md](CONTRIBUTING.md) for development checks, and
[SUPPORT.md](SUPPORT.md) for safe support requests. Planned improvements are
listed in [ROADMAP.md](ROADMAP.md). Maintainers can reuse the
[launch kit](PROMOTION.md) for privacy-accurate project announcements. Public
product updates are recorded in [docs/CHANGELOG.md](docs/CHANGELOG.md).

## License

[MIT](LICENSE)
