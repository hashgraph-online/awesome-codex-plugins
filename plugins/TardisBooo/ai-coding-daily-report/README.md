<div align="center">

# AI Coding Daily Report

**Turn local AI coding sessions into a Markdown daily report with Grok Build, Claude Code, or Codex.**

_Use the `harness-daily` CLI or install its agent plugin._

[![CI](https://github.com/TardisBooo/ai-coding-daily-report/actions/workflows/ci.yml/badge.svg)](https://github.com/TardisBooo/ai-coding-daily-report/actions/workflows/ci.yml)
[![Release](https://github.com/TardisBooo/ai-coding-daily-report/actions/workflows/release.yml/badge.svg)](https://github.com/TardisBooo/ai-coding-daily-report/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-32CD32.svg)](LICENSE)
![Rust](https://img.shields.io/badge/rust-stable-orange)
![Platforms](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-blue)

**English** | [简体中文](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/README.zh-CN.md)

</div>

---

## 📋 Quick Navigation

[Why harness-daily?](#-why-harness-daily) ·
[How it works](#-how-it-works) ·
[Requirements](#-requirements) ·
[Install](#-install) ·
[Install tutorial](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/docs/install.md) ·
[Quick start](#-quick-start) ·
[Commands](#-commands) ·
[Configuration](#-configuration) ·
[Report format](#-report-format) ·
[Extending](#-extending) ·
[Development](#-development) ·
[Contributing](#-contributing) ·
[License](#-license)

---

## 🤔 Why harness-daily?

If you work with multiple AI coding agents — Codex, Claude Code, Grok Build, Pi, OMP, DSH, or Antigravity — your day is
scattered across dozens of sessions in half a dozen projects. Writing a daily standup report means
digging through histories by hand.

harness-daily does it for you:

- **Shared CLI and skill**. The plugin runs with Grok Build, Claude Code, or Codex.
- **Local collection**. The CLI reads supported session logs from disk. Report
  generation passes the report date, project names and paths, and up to 12 prompt
  excerpts of up to 180 characters per project to your selected writer CLI. The
  writer may send them to its configured model provider.
- **Writes the prose with your current agent CLI** — Grok Build, Claude Code, or Codex, using
  the login you already have. No second API key. `init --host auto` picks the first one found.
- **Enterprise-report format** — "today's work" grouped by project with merged work items; raw
  prompts go to an audit appendix, not the summary.
- **Self-healing schedule** — the OS task runs `report --auto --backfill 7`, so a powered-off
  machine at 08:00 still gets its missing reports the next time it boots.

```text
08:00 (OS task) → harness-daily report
   ├─ discover roots  (codex / claude / grok / pi / omp / dsh / antigravity)
   ├─ collect         (parse JSONL, dedupe, drop "continue"/"ok"/smoke-test noise)
   ├─ write            grok --prompt-file / claude -p / codex exec  (your login, your default model)
   └─ render          ~/work-logs/日报-YYYY-MM-DD.md   ← summary · details · issues · stats · audit log
```

## 🧭 How it works

| Piece | Responsibility |
|---|---|
| `harness-daily` (Rust binary) | Discover harness data dirs, parse session logs, aggregate prompts per project, call the writer CLI, render Markdown, install the OS schedule |
| Universal plugin (`skills/`, `commands/`, `plugin.json`, `.claude-plugin/`, `.grok-plugin/`, `plugin.yaml`) | Same repo installs into **Grok Build**, **Claude Code**, or **Codex** |
| Writer host | `grok --prompt-file` · `claude -p --output-format json` · `codex exec` (stdin) |
| OS scheduler | Windows `schtasks` / macOS `launchd` / Linux cron — fires `report --auto --backfill 7` daily |

Supported out of the box: **Codex CLI** (`~/.codex`), **Claude Code** (`~/.claude`), **Grok Build**
(`~/.grok`), **Pi** (`~/.pi`), **OMP** (`~/.omp`), **DSH** (`~/.dsh`), and **Antigravity**
(`~/.gemini/antigravity`, with CLI-store fallback at `~/.gemini/antigravity-cli`). Moved a data dir? Point `[harnesses.<id>].data_dir` at the new location.

## ✅ Requirements

- At least one of [Grok Build](https://x.ai/cli), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), or [Codex CLI](https://github.com/openai/codex), **logged in**
- Windows, macOS, or Linux
- Optional: [Rust](https://rustup.rs) if you build from source

## 📦 Install

Install the binary from a versioned release and verify its SHA-256 digest. Add the
plugin in your host when you want to invoke the CLI from a session.
Follow the [installation guide](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/docs/install.md) · [简体中文](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/docs/install.zh-CN.md).

### Claude Code

```text
/plugin marketplace add TardisBooo/ai-coding-daily-report
/plugin install harness-daily@harness-daily
/harness-daily:setup
```

### Grok Build

```sh
grok plugin install TardisBooo/ai-coding-daily-report@v0.1.1
```

### Codex CLI

```sh
codex plugin marketplace add TardisBooo/ai-coding-daily-report
codex plugin add harness-daily@harness-daily
```

### Binary only

You can follow the [binary installation](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/docs/install.md#install-the-binary) and
initialize the CLI without a plugin.

## 🚀 Quick start

```sh
harness-daily init --host codex --out "<reports-folder>"
harness-daily doctor
harness-daily report --dry-collect
```

Set `--host grok` or `--host claude` to use another installed writer. Run
`harness-daily report` after reviewing the collected prompts. Generate a
specific day or catch up a week:

```sh
harness-daily report --date 2026-09-16
harness-daily report --backfill 7 --auto
```

When you want automatic reports, enable the OS task explicitly:

```sh
harness-daily schedule install --time 08:00
```

## 🎛 Commands

```
harness-daily init --host auto|grok|claude|codex [--out DIR] [--time 08:00]
harness-daily scan                                          list detected harness data roots
harness-daily doctor                                        self-check writer CLI, paths, output dir
harness-daily report [--date D] [--backfill N] [--auto]
                         [--dry-collect] [--out DIR]        generate report(s)
harness-daily schedule install|remove|status|run            manage the OS scheduled task
```

`--auto` skips dates whose report file already exists; `--dry-collect` only writes the collection
JSON (no model call) for debugging.

## ⚙️ Configuration

See [configuration paths](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/docs/install.md#uninstall) for your OS.

```toml
timezone    = "Asia/Shanghai"
output_dir  = '/path/to/work-logs'
report_time = "08:00"
backfill_days = 7
extra_roots = []            # extra scan roots (moved data dirs)

[writer]
host = "auto"               # grok | claude | codex | auto
bin  = ""                   # empty = discover; or an absolute path

[report]
include_audit_log = true    # set false to omit the raw-prompt appendix
include_stats     = true

[harnesses.codex]
enabled  = true
data_dir = ""               # override if you moved ~/.codex

[harnesses.dsh]
enabled  = true
data_dir = ""               # override if you moved ~/.dsh

[harnesses.antigravity]
enabled  = true
data_dir = ""               # override if you moved ~/.gemini/antigravity
```

## 📄 Report format

```markdown
# 工作日报 · 2026-09-16（周三）
## 一、今日工作总结      ← per project, merged work items (no tools, no times)
## 二、工作明细          ← path · time span · completed items
## 三、问题与待办        ← issues the model extracted
## 四、工作量统计        ← sessions / prompts per harness
## 附录：操作审计日志    ← every raw prompt of the day, time-sorted
```

## 🧩 Extending

- **New harness / desktop app**: copy [`adapters/example-jsonl.toml`](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/adapters/example-jsonl.toml)
  into your config dir and edit the paths/keys. Built-in Rust adapters live in `src/collect.rs`;
  PRs welcome (see [`CONTRIBUTING.md`](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/CONTRIBUTING.md)).
- **Writer CLI**: `--host grok|claude|codex|auto`. Collection covers all seven built-in sources.
- **Privacy**. `report --dry-collect` writes the collection locally without
  invoking a writer. The optional audit appendix includes original prompts.

## 🛠 Development

```sh
cargo test                 # unit tests (JSON parsing, timezone bounds, noise filters)
cargo clippy --all-targets -- -D warnings
cargo fmt --check
cargo run -- scan           # try discovery against your real machine
```

Repository layout: `src/collect.rs` (per-harness collectors) · `src/writer.rs` (Grok / Claude /
Codex headless invocation + strict-JSON recovery) · `src/render.rs` (Markdown assembly) ·
`src/schedule.rs` (Windows/macOS/Linux schedulers) · `skills/` + `commands/` + `.claude-plugin/`
+ `.grok-plugin/` + `plugin.yaml` (universal plugin).

## 🤝 Contributing

Bug reports and new-harness adapters are very welcome — see
[CONTRIBUTING.md](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/CONTRIBUTING.md). For security issues, see [SECURITY.md](SECURITY.md).

## 📜 License

[MIT](LICENSE)
