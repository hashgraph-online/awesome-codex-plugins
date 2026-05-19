---
name: ecosystem-health
user-invocable: false
tags: [reference, health, monitoring, ci, endpoints]
model: haiku
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Monitor health across configured service endpoints, CI pipelines, and critical
  issues. Automatically invoked during session-start when ecosystem-health is
  enabled in Session Config.
---

# Ecosystem Health Check

## Platform-native (CC 2.1.105+)

This skill's watcher is registered as a plugin monitor via `.claude-plugin/plugin.json`'s `experimental.monitors` reference to `monitors/monitors.json`. Each session that loads this plugin auto-starts the watcher in the background (see `scripts/lib/ecosystem-health.mjs`). Each NDJSON stdout line from the watcher becomes a `<task_notification>` event Claude sees mid-session.

For harness < 2.1.105 (no monitor support), the skill's manual probes documented below serve as the fallback path.

## Session Config Fields Used

This skill reads from the project's `## Session Config` section in the platform instruction file:

- **`health-endpoints`** — list of `{name, url}` objects for service health checks
- **`cross-repos`** — list of related repositories for critical issue scanning

Both fields are optional. The skill degrades gracefully when either is missing. On Codex this means `AGENTS.md`; on Claude/Cursor it means `CLAUDE.md`.

## Service Health

Read the `health-endpoints` field from Session Config. If not configured or empty, print:

> No health endpoints configured in Session Config. Add `health-endpoints` to enable service monitoring.

and skip this section.

Otherwise, for each configured endpoint, run a health check:

```bash
# Example health-endpoints config:
#   health-endpoints:
#     - name: API
#       url: https://api.example.com/health
#     - name: Worker
#       url: http://worker:8080/healthz
#     - name: Dashboard
#       url: http://localhost:3000/api/health

# For EACH endpoint in health-endpoints, run:
# NAME=<name> URL=<url>
curl -s --max-time 6 -w '\nHTTP_STATUS:%{http_code}' "$URL" 2>/dev/null \
  | python3 -c "
import sys, json
raw = sys.stdin.read()
body, _, status_line = raw.rpartition('\nHTTP_STATUS:')
http_code = int(status_line.strip() or '0')
status = None
try:
    d = json.loads(body)
    if isinstance(d, dict) and 'status' in d:
        bs = str(d['status']).lower()
        status = 'DEGRADED' if bs == 'degraded' else ('OK' if bs in ('ok', 'healthy', 'up') else 'DOWN')
except Exception:
    pass
if status is None:
    status = 'OK' if 200 <= http_code < 400 else 'DOWN'
print(f'\$NAME: {status}')
" 2>/dev/null || echo "\$NAME: unreachable"
```

Generate the check commands dynamically from the config — do not hardcode any service names or URLs.

## Critical Issues Across Projects

Read the `cross-repos` field from Session Config. If not configured or empty, print:

> No cross-repos configured in Session Config. Add `cross-repos` to enable cross-project issue scanning.

and skip this section.

### Detect VCS

> **VCS Reference:** Detect the VCS platform per the "VCS Auto-Detection" section of the gitlab-ops skill.
> Use CLI commands per the "Common CLI Commands" section. For cross-project queries, see "Dynamic Project Resolution."

### For each cross-repo, query critical issues

Using the detected VCS CLI (per gitlab-ops "Common CLI Commands" and "Dynamic Project Resolution" sections):

1. Resolve the project ID or owner/repo slug for each cross-repo
2. Query open issues with `priority:critical` or `priority:high` labels (limit 5 per repo)
3. Collect results across all configured repos

## CI Pipeline Status

Query the latest pipeline/workflow runs for the current repo using the detected VCS CLI (per gitlab-ops "Common CLI Commands" section). Report the 3 most recent runs.

## Report Format

Present as a compact health dashboard. Build the table dynamically from whichever endpoints are configured:

```
## Ecosystem Health
| Service       | Status            |
|---------------|-------------------|
| <name>        | [OK/DEGRADED/DOWN/unreachable]  |
| ...           | ...               |

Critical issues: [N total across cross-repos]
CI: [green/red/pending]
```

If no health endpoints are configured, omit the service table entirely.
If no cross-repos are configured, omit the critical issues line.

Flag any service that is DOWN or DEGRADED, or any critical issue count > 0 as requiring attention.
