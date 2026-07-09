# Cross-Project Coordination

When agents work across multiple repositories (frontend/backend, monorepo, microservices).

---

## Option A: Same Project Key (Simplest)

Use the same `project_key` for related repos. Agents auto-coordinate.

```
# Both agents use same project_key
macro_start_session(
  human_key="/abs/path/monorepo",
  program="codex-cli",
  model="YOUR_MODEL"
)
```

---

## Option B: Separate Projects with Contact Links

For truly separate projects, establish contact links.

### Step 1: Backend Agent Requests Contact

```
request_contact(
  project_key="/abs/path/backend",
  from_agent="GreenCastle",
  to_agent="BlueLake",
  to_project="/abs/path/frontend",
  reason="API coordination"
)
```

### Step 2: Frontend Agent Accepts

```
respond_contact(
  project_key="/abs/path/frontend",
  to_agent="BlueLake",
  from_agent="GreenCastle",
  accept=true
)
```

### Step 3: Cross-Project Messaging

```
send_message(
  project_key="/abs/path/backend",
  sender_name="GreenCastle",
  to=["BlueLake"],
  subject="API contract update",
  body_md="Changed /api/users response schema..."
)
```

---

## Option C: Product Bus (Multi-Repo Products)

Group related projects under a product for unified inbox/search.

### CLI Commands

```bash
# Create product
mcp-agent-mail products ensure MyProduct --name "My Product"

# Link projects
mcp-agent-mail products link MyProduct /abs/path/backend
mcp-agent-mail products link MyProduct /abs/path/frontend

# Product-wide search
mcp-agent-mail products search MyProduct "urgent AND deploy" --limit 50

# Product-wide inbox
mcp-agent-mail products inbox MyProduct GreenCastle --urgent-only

# Product-wide thread summary
mcp-agent-mail products summarize-thread MyProduct "bd-123"
```

---

## Contact Policies

| Policy | Behavior |
|--------|----------|
| `open` | Accept any message (no contact required) |
| `auto` (default) | Allow if shared context exists |
| `contacts_only` | Require explicit approval |
| `block_all` | Reject all cross-project messages |

```
set_contact_policy(project_key, agent_name, "auto")
```

---

## Macro: Contact Handshake

One-call setup with optional auto-accept:

```
macro_contact_handshake(
  project_key="/abs/path/backend",
  requester="GreenCastle",
  target="BlueLake",
  to_project="/abs/path/frontend",
  auto_accept=true,
  welcome_subject="Backend coordination",
  welcome_body="Let's coordinate API changes"
)
```

---

## Cross-Project File Reservations

File reservations are project-scoped. For shared files:

1. Use same `project_key` (Option A), or
2. Coordinate via messages before editing shared paths

```
# In backend project
send_message(
  ...
  subject="Need to edit shared/types.ts",
  body_md="Planning changes to shared types. Any conflicts?"
)
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "CONTACT_BLOCKED" | Run `request_contact`, wait for `respond_contact(accept=true)` |
| Can't find agent | Use `resource://agents/{project_key}` to discover names |
| Messages not arriving | Verify `to_project` is correct absolute path |
| Contact expired | Re-request; default TTL is 7 days |
