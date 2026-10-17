# Event Calendar

**Trigger**: User wants to check important scheduled events in the crypto space — project milestones, policy dates, macroeconomic schedules, token unlocks, and similar date-bound items.
Common phrases: "Any important events coming up", "What's happening this month", "What should I watch in the next 7 days", "Any unlocks next month", "What happened on the calendar last month", "Any scheduled dates for XX".

Difference between event calendar and events:
- Event calendar → editor-compiled event nodes: project launches, policy milestones, macro data releases, etc.
- Events → industry event registrations: summits, hackathons, roadshows

## Steps

### 1. Resolve the time window before querying

Treat time resolution as mandatory for calendar requests. Do not call `list-calendar-events` until the user's time intent has been converted into an explicit query window.

Resolve time intent in this order:

- Explicit date range: if the user gives start and end dates, use that exact range.
- Relative month phrases: interpret "this month" / "本月", "next month" / "下月", and "last month" / "上月" as natural-month windows relative to the current date.
- Rolling windows: interpret phrases such as "next 7 days", "未来7天", "this week ahead", or "coming up soon" as a rolling range from today to the requested future cutoff.
- Open-ended date anchors: interpret "from <date>" or "after <date>" as a lower-bound query starting at that date.
- No clear time hint: ask for or assume the narrowest reasonable window instead of listing the entire calendar from the earliest stored item.

Translate the resolved window into query parameters:

- Natural month windows -> prefer `--period this-month|next-month|last-month`
- Explicit or rolling ranges -> use `--start-from` and `--end-to`
- Lower-bound only requests -> use `--start-from`
- Upper-bound only requests -> use `--end-to`, and treat them as backward-looking unless the user explicitly asks for ascending order

Sorting is secondary to time resolution:

- Use `--order asc` for most upcoming or bounded-window queries
- Use `--order desc` for backward-looking scans, including `--end-to` used on its own, unless the user explicitly asks for ascending order

### 2. List calendar events inside that window

```bash
node cli.mjs list-calendar-events [--period this-month|next-month|last-month] [--search "<keyword>"] [--start-from <YYYY-MM-DD>] [--end-to <YYYY-MM-DD>] [--order asc|desc] [--take 20] --lang <lang>
```

`--period` and explicit date filters are mutually exclusive: use either `--period` or `--start-from`/`--end-to`, not both in the same query.

Examples of time-intent translation:

- "本月有哪些值得关注的事件" -> `--period this-month --order asc`
- "下月有哪些代币解锁" -> `--period next-month --order asc`
- "未来7天的大事和解锁" -> `--start-from <today> --end-to <today+7d> --order asc`
- "回看上月日历" -> `--period last-month --order asc`
- "看截至昨天为止最近有哪些事件" -> `--end-to <yesterday> --order desc`

### 3. Filter a specific date range

```bash
node cli.mjs list-calendar-events --start-from 2025-01-01 --end-to 2025-01-31 --order asc --take 20 --lang <lang>
```

### 4. Browse relative month windows directly

```bash
node cli.mjs list-calendar-events --period this-month --order asc --take 20 --lang <lang>
node cli.mjs list-calendar-events --period next-month --order asc --take 20 --lang <lang>
node cli.mjs list-calendar-events --period last-month --order asc --take 20 --lang <lang>
```

### 5. Query a rolling future window

```bash
node cli.mjs list-calendar-events --start-from <today> --end-to <today+7d> --order asc --take 20 --lang <lang>
```

## Output requirements

- Order by date for a clear timeline view
- Include date, title, and category for each event
- If an article or activity is linked, include its title
- Include external links where available
- For prompts such as "值得关注的大事和代币解锁", resolve the time window first, then highlight those categories inside that window instead of broadening the date range
