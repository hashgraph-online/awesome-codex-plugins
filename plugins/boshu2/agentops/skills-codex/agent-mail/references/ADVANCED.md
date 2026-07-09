# Advanced Agent Mail Features

## Table of Contents
- [Product Bus](#product-bus)
- [Build Slots](#build-slots)
- [Client Integrations](#client-integrations)
- [On-Disk Layout](#on-disk-layout)
- [Database Schema](#database-schema)

---

## Product Bus

Group multiple repositories under a single product for unified inbox/search.

### CLI Commands

```bash
# Ensure product exists
mcp-agent-mail products ensure MyProduct --name "My Product"

# Link project to product
mcp-agent-mail products link MyProduct /abs/path/backend
mcp-agent-mail products link MyProduct /abs/path/frontend

# Product status
mcp-agent-mail products status MyProduct

# Product-wide search
mcp-agent-mail products search MyProduct "urgent AND deploy" --limit 50

# Product-wide inbox
mcp-agent-mail products inbox MyProduct GreenCastle --urgent-only --include-bodies

# Product-wide thread summary
mcp-agent-mail products summarize-thread MyProduct "bd-123"
```

### Use Cases

- Monorepo with multiple packages
- Frontend/backend split repos
- Microservices architecture
- Shared component libraries

---

## Build Slots

Advisory locks for long-running tasks (dev servers, watchers, builds).

### Tools

| Tool | Purpose |
|------|---------|
| `acquire_build_slot(project_key, agent_name, slot, ttl_seconds?, exclusive?)` | Acquire slot |
| `renew_build_slot(project_key, agent_name, slot, extend_seconds?)` | Extend TTL |
| `release_build_slot(project_key, agent_name, slot)` | Release slot |

### CLI Helpers

```bash
# Print environment keys for scripts
mcp-agent-mail amctl env --path . --agent GreenCastle

# Wrap command with env keys set
mcp-agent-mail am-run frontend-build -- npm run dev
```

### Example Workflow

```
1. Acquire slot:    acquire_build_slot(project_key, agent_name, "dev-server", ttl_seconds=3600)
2. Start process:   npm run dev
3. Renew as needed: renew_build_slot(project_key, agent_name, "dev-server", extend_seconds=1800)
4. Release on exit: release_build_slot(project_key, agent_name, "dev-server")
```

---

## Client Integrations

### Claude Code

Integration script: `scripts/integrate_claude_code.sh`

- Configures `.claude/settings.json`
- Installs hooks for inbox reminders
- MCP server configuration

**Hooks for Inbox Reminders:**
- Fire after tool invocations
- Rate limited to once per 2 minutes
- Uses fast curl calls (no Python import overhead)

### Codex CLI

Integration script: `scripts/integrate_codex_cli.sh`

- Configures `~/.codex/config.toml`
- Uses `notify` handler for reminders

### Gemini CLI

Integration script: `scripts/integrate_gemini_cli.sh`

- Configures `~/.gemini/settings.json`

### Automatic Inbox Reminders

All integrations support inbox reminder hooks:

```json
{
  "hooks": {
    "post_tool_call": [
      {
        "command": "curl -s http://127.0.0.1:8765/api/inbox-reminder?agent=${AGENT_NAME}",
        "rate_limit_seconds": 120
      }
    ]
  }
}
```

---

## On-Disk Layout

```
<STORAGE_ROOT>/projects/<slug>/
  agents/<AgentName>/profile.json
  agents/<AgentName>/inbox/YYYY/MM/<msg-id>.md
  agents/<AgentName>/outbox/YYYY/MM/<msg-id>.md
  messages/YYYY/MM/<msg-id>.md
  messages/threads/<thread-id>.md  # optional digest
  file_reservations/<sha1-of-path>.json
  attachments/<xx>/<sha1>.webp
  build_slots/<slot>/<agent>__<branch>.json
```

### Message File Format

GFM Markdown with JSON frontmatter:

```markdown
---json
{
  "id": 1234,
  "thread_id": "TKT-123",
  "project": "/abs/path/backend",
  "from": "GreenCastle",
  "to": ["BlueLake"],
  "created": "2025-10-23T15:22:14Z",
  "importance": "high",
  "ack_required": true
}
---

# Message subject

Message body in markdown...
```

### File Reservation Format

```json
{
  "id": 101,
  "agent": "GreenCastle",
  "path_pattern": "src/auth/**/*.ts",
  "exclusive": true,
  "reason": "bd-123",
  "created_ts": "2025-10-23T15:00:00Z",
  "expires_ts": "2025-10-23T16:00:00Z"
}
```

---

## Database Schema

SQLite with FTS5 for full-text search.

### Core Tables

```sql
projects(id, human_key, slug, created_at)

agents(id, project_id, name, program, model, task_description,
       inception_ts, last_active_ts, attachments_policy, contact_policy)

messages(id, project_id, sender_id, thread_id, subject, body_md,
         created_ts, importance, ack_required, attachments)

message_recipients(message_id, agent_id, kind, read_ts, ack_ts)

file_reservations(id, project_id, agent_id, path_pattern, exclusive,
                  reason, created_ts, expires_ts, released_ts)

agent_links(id, a_project_id, a_agent_id, b_project_id, b_agent_id,
            status, reason, created_ts, updated_ts, expires_ts)
```

### FTS Index

```sql
fts_messages(message_id UNINDEXED, subject, body)
-- Auto-maintained via triggers on messages table
```

### Key Relationships

- `agents.project_id` → `projects.id`
- `messages.project_id` → `projects.id`
- `messages.sender_id` → `agents.id`
- `message_recipients.message_id` → `messages.id`
- `message_recipients.agent_id` → `agents.id`
- `file_reservations.project_id` → `projects.id`
- `file_reservations.agent_id` → `agents.id`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_ROOT` | `~/.mcp_agent_mail_git_mailbox_repo` | Root for repos + SQLite |
| `HTTP_PORT` | `8765` | Server port |
| `HTTP_BEARER_TOKEN` | — | Static bearer token |
| `HTTP_JWT_ENABLED` | `false` | Enable JWT validation |
| `LLM_ENABLED` | `true` | Enable LLM summaries |
| `LLM_DEFAULT_MODEL` | `gpt-5-mini` | LLM model for summaries |
| `CONTACT_ENFORCEMENT_ENABLED` | `true` | Enforce contact policy |
| `INLINE_IMAGE_MAX_BYTES` | `65536` | Threshold for inlining WebP |
| `FILE_RESERVATION_INACTIVITY_SECONDS` | `1800` | Staleness threshold |

---

## Git-Based Project Identity

### Worktree Mode

For git worktrees, Agent Mail can resolve identity from path markers:

```
resource://identity/{path}
```

### Identity Modes

| Mode | Behavior |
|------|----------|
| `strict` | Reject invalid agent names |
| `coerce` | Auto-generate if invalid |
| `always_auto` | Always auto-generate names |

### Project Adoption

For linking existing repositories to Agent Mail projects:

```bash
# During project ensure, specify identity mode
ensure_project(human_key="/abs/path", identity_mode="coerce")
```
