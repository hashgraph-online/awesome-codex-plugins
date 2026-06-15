---
name: mcp-connector-bridge
description: "Active MCP connector polling that integrates external tools (issue trackers, error monitoring, CI) into the heartbeat loop for cross-system discovery."
origin: ECC
---

# MCP Connector Bridge

Active MCP connector polling that integrates external tools into the heartbeat loop.
The difference between an agent that says "here is the fix" vs a loop that opens
the PR, links the ticket, and pings the channel — by itself.

## When to Activate

- User configures `.claude/connectors.yaml` with active MCP servers
- Heartbeat scheduler includes connector-based scans
- User invokes `/heartbeat start` with connector scans configured
- External event triggers a connector poll

## Core Concept

MCP connectors let the loop touch real tools: issue trackers, error monitoring,
databases, CI systems, chat platforms. Without connectors, the loop is isolated
to the local repo. With connectors, it can discover issues from anywhere.

```
Heartbeat tick
  │
  ├─ Local scans (test, lint, type-check)
  │
  └─ Connector scans (MCP servers)
       ├─ GitHub: "List open issues assigned to me"
       ├─ Sentry: "List unresolved errors in last 24h"
       └─ Linear: "List my in-progress tasks stale >7d"
```

## Configuration

Create `.claude/connectors.yaml`:

```yaml
connectors:
  - name: "github-issues"
    server: "github"
    heartbeatScan: "List open issues assigned to me with label:bug"
    triageOnNew: true
    priority: "medium"

  - name: "sentry-errors"
    server: "sentry"
    heartbeatScan: "List unresolved errors from last 24 hours"
    triageOnNew: true
    priority: "high"

  - name: "linear-tasks"
    server: "linear"
    heartbeatScan: "List my in-progress tasks not updated in 7 days"
    autoGoalOnStale: "7d"
    priority: "low"

  - name: "slack-mentions"
    server: "slack"
    heartbeatScan: "Check unread mentions in engineering channel"
    triageOnNew: true
    priority: "low"
```

## Connector Scan Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique connector identifier |
| `server` | Yes | MCP server name (must be configured in mcp-configs/) |
| `heartbeatScan` | Yes | Prompt to send to the MCP server |
| `triageOnNew` | No | Create triage items for new findings |
| `autoGoalOnStale` | No | Auto-create goal if stale beyond duration |
| `priority` | No | Default severity for triage items (high/medium/low) |
| `enabled` | No | Disable without removing (default: true) |

## Health Check

Before polling, verify connector is reachable:

1. Check MCP server is configured in project MCP settings
2. Verify server responds to basic query
3. If unreachable: skip this connector, log warning
4. If reachable: execute heartbeatScan prompt

Builds on existing `pre:mcp-health-check` hook.

## Result Classification

Connector scan results follow the same classification as local scans:

| Finding | Action |
|---------|--------|
| New issue discovered | → Triage item (if `triageOnNew: true`) |
| Stale task detected | → Auto-goal (if `autoGoalOnStale` configured) |
| No new findings | → Skip silently |
| Connection failed | → Log warning, skip |

## Integration Points

- **`/heartbeat`**: Connector scans run alongside local scans during each tick
- **`/triage`**: New connector findings populate the triage inbox
- **`/goal`**: Stale task connectors can auto-create goals
- **`mcp-configs/`**: Connector references must match configured MCP servers
- **MCP health hook**: Validates connectivity before scan

## Hard Bans

- Connectors MUST NOT write to external systems during discovery (read-only scans)
- Failed connections MUST NOT block local heartbeat scans
- Connector output MUST be size-limited (prevent token overflow from large responses)
- Credentials MUST NOT be stored in connectors.yaml (use MCP server config)
- Polling frequency MUST respect rate limits of external services

## Example Flow

```
Heartbeat tick (every 30m):
  Local scans: ✓ tests pass, ✓ lint clean
  Connector scans:
    github-issues: Found 2 new bugs → triage inbox
    sentry-errors: No new errors → skip
    linear-tasks: 1 task stale 10 days → auto-goal created

Result:
  2 triage items created from GitHub
  1 goal created from Linear stale task
  Total: 3 actions from this tick
```
