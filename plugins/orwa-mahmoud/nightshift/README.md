# Nightshift

Nightshift is a plugin for Claude Code, Codex, and Cursor. Plan the work with the agent in the plan
room, step away while it works the punch list until every item is checked off, and come back to a
receipt for each item: what was delivered, which checks ran, the evidence you asked for, and its
working time and token usage.

- **Plan:** brainstorm in the plan room while your code stays read-only. The agent shapes the
  conversation into a punch list and offers evidence, an edge-case pass, a pre-mortem, and research.
- **Execute:** work an agreed list, or give Hunt a goal and the hours. Thirty-two ready-made shifts
  mean you don't need a backlog. Decisions are parked with a default so the work keeps going.
- **Review:** read the morning receipt, follow each item to its receipt, then archive the shift.
  Open items and unanswered decisions stay live for the next one.

It installs as a native plugin, with no separate app, service, or API key, and runs on macOS, Linux,
and Windows.

## Install

Claude Code:

```text
/plugin marketplace add orwa-mahmoud/nightshift
/plugin install nightshift@nightshift
```

Codex:

```text
codex plugin marketplace add orwa-mahmoud/nightshift
codex plugin add nightshift@nightshift
```

Then review and trust its hooks, with `/hooks` in the CLI or, in the Codex app, the **Review hooks**
button (the hook icon in the message box) or **Settings → Hooks**.

Cursor: open **Customize → Add → From GitHub Repository**, paste
`https://github.com/orwa-mahmoud/nightshift`, choose a scope, and select **Import**. Then select
Nightshift from the imported marketplace to install it.

## First shift

1. Open the project you want to work on and run `/nightshift:setup`. Answer a few questions to set
   your preferences.
2. Run `/nightshift:plan` and describe the work in your own words. Approve the items you want.
3. Run `/nightshift:start`. Watch the first shift, then review its changes and receipts before you
   publish anything.

## Read more

- [README](https://github.com/orwa-mahmoud/nightshift#readme) — the full tour.
- [Setup](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/setup.md) and [the plan room](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/plan-room.md).
- [Shift modes and ready-made shifts](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/shift-modes.md).
- [Evidence](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/evidence.md) and [item budgets](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/item-budgets.md).
- [Receipts and token usage](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/receipts.md) and [Archive and continue](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/archive.md).
- [Documentation](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/README.md) and [website](https://nightshift.orwamahmoud.com/).

Security reporting: [SECURITY.md](SECURITY.md#security-policy). License: [LICENSE](LICENSE).
