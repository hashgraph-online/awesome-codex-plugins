---
name: garmin-health-data
description: Use when building or running a Garmin Connect health-data workflow with python-garminconnect, including China-region Garmin accounts, token-safe authentication, daily summaries, sleep, HRV, resting heart rate, stress, training readiness, training status, running activities, Garmin Coach training plans, and weekly training reports.
---

# Garmin Health Data

Use this skill when a user wants to fetch, validate, summarize, or analyze Garmin Connect data with a local script-first workflow.

## Scope

This skill covers:

- Garmin Connect authentication and token handling.
- China-region accounts with `Garmin(is_cn=True)`.
- Lightweight daily summaries: steps, sleep, HRV, resting heart rate, stress, training readiness, and training status.
- Recent running activity summaries.
- Garmin Coach / adaptive training-plan summaries.
- Conservative weekly training reports.

This skill does not provide medical diagnosis and should not default to aggressive training plans.

## Safety Rules

- Never write Garmin email, password, one-time verification codes, OAuth tokens, cookies, or raw identifying API payloads into a repository, note vault, report, or chat.
- Store Garmin tokens outside the project by default, normally under `~/.garminconnect`.
- Set token file permissions to owner-only when possible, for example `chmod 600 ~/.garminconnect/garmin_tokens.json`.
- Save lightweight summaries before LLM analysis. Do not feed raw full time-series payloads to a model by default.
- Do not download FIT / GPX / TCX files unless the user explicitly requests detailed activity, lap, route, or mechanics analysis.
- Use placeholders in docs and public artifacts: `<workspace>`, `<tokenstore>`, `<email>`, `<host>`, `<date>`.

## Recommended Workspace Shape

Use a local project directory such as `<workspace>/Garmin`:

```text
Garmin/
  scripts/
  data/
  cache/
  reports/
  docs/
```

Prefer a project virtual environment for repeated use:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install --upgrade garminconnect curl_cffi pandas rich
```

If China-region support is needed, verify the installed `garminconnect` version uses `diauth.garmin.cn` when `Garmin(is_cn=True)`. If the released PyPI package is stale, install from the upstream GitHub repository and document that choice without pinning private local paths.

## Authentication Workflow

1. Try loading tokens from `~/.garminconnect`.
2. If tokens are missing or expired, authenticate locally with hidden password input or OS-native secure prompts.
3. For China-region accounts, construct the client with `Garmin(is_cn=True)`.
4. If MFA is required, collect the code interactively and never store it.
5. After successful login, verify a tiny read such as `get_stats(<today>)`.
6. Save token metadata only through the library token store, outside the project.

China-region caveat:

- Some library versions start with a mobile login flow. With MFA, that flow can try to consume a ticket through `mobile.integration.garmin.com`, which may not resolve in some environments.
- If that happens, use a portal-login strategy against the region-aware Garmin portal and then dump tokens. Do not patch installed dependencies silently; keep any workaround in a local script and document why it exists.

## Data Fetch Workflow

For a normal weekly summary:

```bash
source .venv/bin/activate
python Garmin/scripts/fetch_recent_daily.py --days 7
python Garmin/scripts/fetch_recent_activities.py --days 28
python Garmin/scripts/fetch_training_plans.py --days-back 7 --days-ahead 14
python Garmin/scripts/generate_weekly_report.py
```

Daily summary should call each endpoint independently and record `ok / missing / error`:

- `get_stats`
- `get_sleep_data`
- `get_hrv_data`
- `get_rhr_day`
- `get_stress_data`
- `get_training_readiness`
- `get_training_status`

Running activities should use `get_activities_by_date` and save only summary fields by default:

- activity id and name
- activity type
- local start time
- distance
- duration and moving duration
- average and max heart rate
- pace or average speed
- elevation gain
- training effect
- anaerobic training effect
- activity training load
- recovery time

## Garmin Coach / Training Plans

Use `get_training_plans()` to list plans.

For Garmin Coach / adaptive running plans, use:

```python
client.get_adaptive_training_plan_by_id(plan_id)
```

Do not assume `get_training_plan_by_id(plan_id)` works for Coach plans; adaptive plans can return `400 Not a phased plan` on the ordinary phased-plan endpoint.

Training-plan summaries should keep only compact fields:

- plan id
- plan name
- training type and subtype
- status
- start and end dates
- nearby task dates
- workout name
- sport type
- rest-day flag
- estimated duration
- estimated distance
- training effect label
- completion status if available

Avoid saving full raw plan payloads unless the user explicitly needs schema exploration.

## Weekly Report Contract

Default report destination:

```text
Garmin/reports/YYYY-MM-DD Garmin training weekly report.md
```

Recommended sections:

- `One-line conclusion`
- `Training completed this week`
- `Garmin Coach / planned tasks`
- `Recovery status`
- `Risk signals`
- `Next-week suggestions`
- `Needs continued observation`
- `Data sources`

Keep suggestions conservative:

- If sleep, HRV, resting heart rate, soreness, or training readiness are poor, prioritize recovery and lower intensity.
- Keep long-term race goals as context, not an excuse to force a training plan into every report.
- Clearly mark missing Garmin fields instead of guessing.

## Validation Checklist

After editing local scripts:

```bash
python -m py_compile Garmin/scripts/*.py
```

Before using data in a report:

- Confirm token file exists outside the project and is not tracked.
- Confirm each daily endpoint has `ok / missing / error`.
- Confirm the weekly report's activity totals are filtered to the report date range, not the full activity fetch window.
- Confirm training-plan summaries are compact and do not contain credentials or personal identifiers.
- Confirm no FIT / GPX / TCX files were downloaded unless explicitly requested.
