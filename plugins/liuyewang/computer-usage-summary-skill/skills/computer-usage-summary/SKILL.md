---
name: computer-usage-summary
description: Summarize what a user did on macOS, Windows, or Linux using local ActivityWatch records, with privacy-preserving live-state and Screen Time fallbacks when records are unavailable. Use for daily activity summaries, app usage time, foreground sessions, AFK time, timelines, and paste-ready spreadsheet tables.
---

# Computer Usage Summary

## Overview

Use local ActivityWatch data first. This skill supports macOS, Windows, and
Linux wherever the local ActivityWatch API and Python 3.9+ are available. The
intended privacy-balanced setup records
only foreground apps, sanitized window titles, and AFK state. Do not install
browser extensions, enable `aw-sync`, configure cloud storage, or expose the
local API.

Accurate historical app time and AFK time exist only from the time
ActivityWatch starts recording. Do not infer them from process uptime, macOS
system logs, browser history, or undocumented databases.

## Setup And Verification

Use this section only when ActivityWatch is missing, stopped, or needs repair.

1. Inspect the local ActivityWatch application, its startup setting, local
   processes, and the current user's ActivityWatch data directory. Do not
   replace a working installation.
2. Let the user choose an official installation source. Before launching it or
   enabling automatic startup, verify the publisher and operating-system
   security status. On macOS, use `codesign --verify --deep --strict` and
   `spctl --assess --type execute`. Stop if validation fails unless the user
   explicitly decides otherwise.
3. Enable only the window and AFK watchers. Let macOS request Accessibility
   permission through its normal interface; never bypass or change privacy
   permissions programmatically.
4. On Windows, install the bundled `requirements.txt` once so Python can
   resolve IANA time zones such as `Asia/Singapore` consistently.
5. Confirm the local `http://127.0.0.1:5600` server has `currentwindow` and
   `afkstatus` buckets containing events. The default AFK threshold is 180
   seconds.

## No-ActivityWatch Fallback

When the app, local API, buckets, or requested-range events are unavailable:

- Mark active time, AFK time, sessions, and launch counts as `unavailable`,
  not zero.
- A current frontmost-app or running-app snapshot is only evidence of the
  present, not the requested range.
- Use Screen Time only when the user makes its visible totals available; label
  it `Screen Time reported` and do not read private databases.
- Inspect browser history only for an explicit website-level request. Inspect
  recent documents or terminal history only after explicit, source-specific
  permission. Treat all such results as metadata clues, not durations.

## Workflow

1. Establish the local date range and time zone.
2. Run `scripts/activitywatch_summary.py --date today`, use `--period week` or
   `--period month` around an anchor date, or use inclusive `--start YYYY-MM-DD
   --end YYYY-MM-DD` dates. Add `--timezone Area/City` for reproducible local
   timestamps. Keep `--api-url` on the loopback interface.
3. Use `active_seconds` and `afk_seconds` only when ActivityWatch confirms
   them. Describe `foreground_sessions` as observed foreground intervals, not
   process launches.
4. Use sanitized app names and window titles to reconstruct the timeline. A
   title is `confirmed` only when it directly supports the described activity.
5. When the user needs project/client or billable reporting, offer an optional
   local JSON `--rules` file. Match only sanitized titles. Explain that the
   first matching rule wins and never create or upload rules without consent.
6. For spreadsheet output, run one table per command:
   - `--format markdown --table apps` for chat.
   - `--format tsv --table apps` to copy directly into spreadsheet software.
   - `--format tsv --table timeline` for chronological rows.
   - `--format csv --table apps --csv-bom --output report.csv` for an
     Excel-friendly file, only when the user asks to save one.
   - `--report client-timesheet` for project/client billable rows.
   - `--report weekly-review` for a compact review table.
   - `--report app-trend` for local daily trend rows.
7. When ActivityWatch is unavailable, return its structured reason. Markdown,
   TSV, and CSV outputs provide `status`, `reason`, and `source` columns.

## Privacy Rules

- Treat window titles as sensitive. Remove URLs, truncate long titles, and
  never include complete browser URLs.
- Keep default sanitized titles for a useful timeline; use `--hide-titles` if
  the user wants a title-free export.
- Use the smallest useful amount of title context; application and summary
  tables do not need titles.
- Escape spreadsheet cells that could be interpreted as formulas.
- Keep reports local to the current conversation. Do not export, upload, or
  share activity data without explicit user approval.
