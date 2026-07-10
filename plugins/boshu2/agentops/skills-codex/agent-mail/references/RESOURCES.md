# MCP Resources Reference

Fast read-only access to Agent Mail data via MCP resources.

---

## Inbox & Outbox

### Inbox
```
resource://inbox/{agent}?project=<path>&limit=20&include_bodies=true
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `project` | Yes | — | Absolute path to project |
| `limit` | No | 20 | Max messages to return |
| `include_bodies` | No | false | Include full message bodies |
| `since_ts` | No | — | ISO-8601 timestamp filter |
| `urgent_only` | No | false | Only high/urgent messages |

### Outbox
```
resource://outbox/{agent}?project=<path>&limit=20
```

Same parameters as inbox.

### Combined Mailbox
```
resource://mailbox/{agent}?project=<path>&limit=20
```

Returns both sent and received messages.

---

## Messages & Threads

### Single Message
```
resource://message/{id}?project=<path>
```

### Thread
```
resource://thread/{thread_id}?project=<path>&include_bodies=true
```

| Parameter | Required | Default |
|-----------|----------|---------|
| `project` | Yes | — |
| `include_bodies` | No | true |
| `limit` | No | 100 |

---

## Agents & Projects

### List Agents in Project
```
resource://agents/{project_key}
```

Returns all registered agents with their current task descriptions.

### Project Details
```
resource://project/{slug}
```

### All Projects
```
resource://projects
```

---

## File Reservations

### Active Reservations
```
resource://file_reservations/{slug}?active_only=true
```

| Parameter | Default |
|-----------|---------|
| `active_only` | true |

### File Reservation by ID
```
resource://file_reservation/{id}?project=<path>
```

---

## Views (Filtered Queries)

### Urgent Unread
```
resource://views/urgent-unread/{agent}?project=<path>
```

High/urgent messages not yet read.

### ACK Required
```
resource://views/ack-required/{agent}?project=<path>
```

Messages with `ack_required=true` awaiting acknowledgment.

### ACK Overdue
```
resource://views/ack-overdue/{agent}?project=<path>&ttl_minutes=30
```

ACK-required messages older than TTL without acknowledgment.

---

## Tooling Metadata

### Tool Directory
```
resource://tooling/directory
```

Grouped tool clusters with playbooks and descriptions.

### Argument Schemas
```
resource://tooling/schemas
```

Parameter hints for all tools.

### Usage Metrics
```
resource://tooling/metrics
```

Call counts and error rates.

---

## Identity (Worktree Mode)

```
resource://identity/{path}
```

For git worktree deployments, resolves agent identity from path markers.

---

## Example Usage

```python
# In your agent code, read resources via MCP
inbox = await mcp.read_resource("resource://inbox/GreenCastle?project=/abs/path&limit=5")

thread = await mcp.read_resource("resource://thread/bd-123?project=/abs/path")

agents = await mcp.read_resource("resource://agents//abs/path/project")
```

---

## Notes

- Resources are read-only; use tools for mutations
- All project paths must be absolute
- Resources return JSON by default
- Missing resources return empty arrays/objects, not errors
