# Nightshift

**Give the agent a shift. Come back to work you can review.**

Nightshift gives Claude Code, Codex, and Cursor a durable work contract for long coding runs.
Bring a task list, choose a ready-made shift, or give your agent an objective and hours to work.
Hooks hold unfinished work at clock-out, a watchman can recover failed sessions, and progress and
decisions stay on disk. Review the results, per-item token usage and time where available, then
archive the shift with its evidence intact.

- **Choose the work:** Hunt and Quality offer ready-made shifts, Guided or Automatic selection,
  and review-first or immediate execution.
- **Work for hours:** product evolution, coverage hunts, and owner-defined walkthroughs preserve
  the current work and exact next action across sessions. Each has an explicit ending.
- **See progress and usage:** the shift report updates during work; the runtime adds per-item
  tokens and duration from host records, marking unavailable measurements explicitly.
- **Keep useful history:** archive finished shifts with linked reports and evidence, while open
  items and unanswered decisions remain live. Automatic filing is optional.

MIT licensed. Bash on macOS and Linux, PowerShell on native Windows. No separate service or API key.
Ticks remain self-reported; the item checks and your review determine whether the work is good.

## Install

Codex and ChatGPT: the
[official OpenAI Plugin Directory](https://chatgpt.com/plugins/plugins_6a7c58f65d708191b3a705a8625baffe),
or from the marketplace for local Codex development:

```text
codex plugin marketplace add orwa-mahmoud/nightshift
codex plugin add nightshift@nightshift
```

Claude Code:

```text
/plugin marketplace add orwa-mahmoud/nightshift
/plugin install nightshift
```

Cursor: open **Customize → Add → From GitHub Repository**, paste
`https://github.com/orwa-mahmoud/nightshift`, choose a scope, and select **Import**.
Then select Nightshift from the imported marketplace to install it.
The [Cursor Directory listing](https://cursor.directory/plugins/nightshift) is for discovery.
Read the [recovery and CLI limitations](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/how-it-works.md#recovery) before starting a shift.

## First shift

Open the project you want Nightshift to change: a Git repository or a persistent folder.
Disposable ChatGPT scratch workspaces are not supported.

1. Ask **“Set up Nightshift in this project”** in Codex; use `/nightshift:setup` in
   Claude Code. Review the proposed checks and permissions.
2. Add one small task under `## Items` in `.nightshift/punch-list.md`, with an outcome and a way
   to verify it. The [first-shift guide](https://github.com/orwa-mahmoud/nightshift#your-first-shift)
   has a filled example.
3. Ask **“Start the Nightshift shift”**, or use `/nightshift:start` in Claude Code. Keep this first
   run attended, then review its changes and report before publishing anything.

## Read more

- [Why Nightshift exists](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/why-nightshift.md) — the screen and the failures behind the design.
- [Choose the work](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/shift-modes.md) — an approved list, a catalog entry, or a goal with a clock.
- [Shift report and token usage](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/shift-report.md) — progress, measurements, and host limits.
- [Archive and continue](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/archive.md) — keep finished history and the next shift's work.
- [Real shifts and reviewed results](https://github.com/orwa-mahmoud/nightshift/blob/main/examples/README.md).
- [Documentation](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/README.md) and [website](https://nightshift.orwamahmoud.com/).

Security reporting: [SECURITY.md](SECURITY.md#security-policy). License: [LICENSE](LICENSE).
