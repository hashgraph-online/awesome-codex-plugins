---
name: computer-usage-summary
description: Use when the user asks what they did on a Mac, requests a daily or multi-day ActivityWatch report, needs foreground app time, browser page or tab summaries, local-time activity timelines, or copyable Markdown, TSV, or CSV usage tables.
---

# Computer Usage Summary

## Overview

Use local ActivityWatch data to produce an evidence-based, table-first report of what the user did. Report daily focus, specific activities, local time windows, application usage, and observed foreground browser pages.

This installation records foreground applications, window titles, and AFK status. It does not use browser extensions, cloud sync, browser history, or complete browser URLs.

## Core Rules

1. Treat the requested dates as local calendar days.
2. Resolve the Mac system IANA timezone and state it with the UTC offset. Only an explicit --timezone value may override the system timezone.
3. Convert every displayed timestamp to that timezone. Do not display raw UTC timestamps in a human report.
4. Merge duplicate and overlapping AFK intervals before calculating time.
5. Keep each day's active, away, and coverage values at or below 24 hours, or below the shorter local day during a daylight-saving transition.
6. Report untracked time separately. Do not relabel missing coverage as away time.
7. Treat foreground_sessions as observed foreground intervals, not process launches.
8. Treat browser rows as observed foreground pages, not a list of every open browser tab.

## Workflow

1. Establish the inclusive local date range and state the timezone.
2. Run the bundled script:

~~~bash
python3 scripts/activitywatch_summary.py --date today
~~~

The default command returns a complete copyable Markdown report.

For a multi-day report:

~~~bash
python3 scripts/activitywatch_summary.py --start YYYY-MM-DD --end YYYY-MM-DD
~~~

For structured model analysis, request JSON explicitly:

~~~bash
python3 scripts/activitywatch_summary.py --start YYYY-MM-DD --end YYYY-MM-DD --format json
~~~

For copyable or spreadsheet-ready tables:

~~~bash
python3 scripts/activitywatch_summary.py --start YYYY-MM-DD --end YYYY-MM-DD --format markdown --table daily
python3 scripts/activitywatch_summary.py --start YYYY-MM-DD --end YYYY-MM-DD --format tsv --table apps
python3 scripts/activitywatch_summary.py --start YYYY-MM-DD --end YYYY-MM-DD --format tsv --table browser
python3 scripts/activitywatch_summary.py --start YYYY-MM-DD --end YYYY-MM-DD --format tsv --table timeline
~~~

Use --timezone Area/City only when the user explicitly requests a timezone different from the Mac system timezone.

Use --min-tab-seconds 120 for a compact browser table. The default value is 0, which includes every normalized foreground browser page.

3. Use JSON data to reconstruct daily activities from application names and sanitized titles.
4. Mark an activity confirmed when a title directly supports it. Otherwise mark it unknown context.
5. Keep exact time ranges and accumulated foreground duration distinct:
   - first_seen to last_active is an observation span and may contain gaps.
   - active_duration is accumulated confirmed foreground time.
6. If ActivityWatch is unavailable or empty, use the fallback workflow and label unavailable metrics.

## Required Output Contract

Return a copyable Markdown report in this order.

### 1. Scope

State:

- Inclusive local dates
- IANA timezone and UTC offset
- Evidence source
- Coverage limitations

### 2. Daily Overview Table

Include one row per day with:

| Field | Meaning |
|---|---|
| Date | Local calendar date |
| First-last observed activity | Observation span, not continuous work |
| Active time | Merged not-afk time |
| Away time | Covered time not classified as active |
| Untracked time | Time outside ActivityWatch coverage |
| Main focus | Best-supported daily theme |

Include a total row for multi-day reports.

### 3. Daily Activity Timeline

Include one copyable table per day with:

| Field | Meaning |
|---|---|
| Start-end | Local time window |
| Main activity | Short category |
| Specific work | Concrete action supported by titles |
| Application or page | Sanitized evidence |
| Confidence | confirmed or unknown context |
| Source | ActivityWatch |

Activities may overlap when the user switched repeatedly between related applications. Do not describe first-to-last spans as continuous focus.

### 4. Application Table

Include application, foreground sessions, numeric active seconds, HH:MM:SS duration, first seen, last active, and source.

For a multi-day report, show the leading applications per day. Include all applications when the user asks for a full export.

### 5. Browser Foreground Page Table

Include:

| Field | Meaning |
|---|---|
| Browser | Chrome, Safari, Firefox, Edge, Brave, Arc, or another detected browser |
| Page title | Sanitized and normalized foreground title |
| What it was for | Activity inferred from the title; use unknown context when unsupported |
| First seen | Local timestamp |
| Last active | Local timestamp |
| Foreground sessions | Distinct observed foreground intervals |
| Active seconds | Numeric accumulated time |
| Active duration | HH:MM:SS accumulated time |
| Source | ActivityWatch foreground window title |

Group repeated observations by browser and normalized title. Remove browser-profile suffixes, memory-usage suffixes, invisible formatting characters, and duplicate watcher heartbeats.

For a readable default chat report, list pages with at least two minutes of accumulated foreground time and add a short-visit table containing the omitted page count and total duration. If the user asks for every page or every tab, list all rows with no duration threshold.

Explain that ActivityWatch cannot identify background tabs, tabs never brought to the foreground, or two same-title tabs as separate objects.

### 6. Caveats

State:

- Foreground sessions are not application launch counts.
- First-to-last spans are not continuous use.
- Tracking covers only periods when ActivityWatch was running.
- Browser data covers foreground titles only and does not come from browser history.

## Table Export

- Markdown is the default human-facing format.
- TSV is the preferred paste-ready format for Excel, Numbers, and Feishu Sheets.
- CSV is available for import workflows.
- Include numeric seconds and HH:MM:SS durations.
- Escape cells beginning with =, +, -, or @.
- Do not save, upload, or share a report unless the user explicitly asks.

## Local Data and Recovery

- ActivityWatch stores local data under ~/Library/Application Support/activitywatch/.
- Use only http://127.0.0.1:5600; never expose the service beyond the Mac.
- If the server or required buckets are unavailable, report the condition and offer repair.
- Do not derive historical duration from process uptime, application start time, browser history, terminal history, or unified logs.

## No-ActivityWatch Fallback

1. State that historical foreground time, AFK time, and sessions are unavailable.
2. If useful, report the current frontmost application and currently running user applications as a live snapshot only.
3. Use Screen Time only when the user shares values visible in its App & Website Activity view. Label them Screen Time reported.
4. Inspect browser history, terminal history, or recent documents only after explicit permission for that source. Treat timestamps as clues, not durations.
5. Explain that ActivityWatch cannot reconstruct time before tracking began.

## ActivityWatch Setup

Use this section only when ActivityWatch is missing, stopped, or the user asks to install or repair it.

1. Inspect /Applications/ActivityWatch.app, running processes, Login Items, and ~/Library/Application Support/activitywatch/.
2. Do not reinstall or replace a working installation.
3. Use one installation channel. Prefer Homebrew stable builds when compatible; use official releases otherwise.
4. Verify with codesign --verify --deep --strict and spctl --assess --type execute before launching an unfamiliar build.
5. Start only the built-in window and AFK watchers by default.
6. Do not enable browser extensions, sync, cloud storage, exports, or additional watchers without explicit permission.
7. Let macOS request Accessibility permission through its normal interface.
8. Confirm the local server, currentwindow bucket, afkstatus bucket, and sample events before claiming tracking works.

## Privacy Rules

- Include the minimum useful title context.
- Never output browser URLs. Replace URL-like titles with [URL omitted].
- Redact titles that reveal passwords, API keys, payment identifiers, identity documents, banking details, or raw user data.
- Do not inspect browser history, terminal history, recent documents, or undocumented system databases without source-specific permission.
- Keep reports local to the current conversation unless the user explicitly requests an export.
