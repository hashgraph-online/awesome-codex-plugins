# Agent Mail Tools Reference

## Table of Contents
- [Project & Identity](#project--identity)
- [Messaging](#messaging)
- [File Reservations](#file-reservations)
- [Contact Management](#contact-management)
- [Macros](#macros)
- [Guard Tools](#guard-tools)
- [Health](#health)

---

## Project & Identity

### ensure_project

Create/ensure project exists.

```
ensure_project(human_key="/abs/path/to/project")
```

**Returns:** `{id, slug, human_key, created_at}`

### register_agent

Register identity in project.

```
register_agent(
  project_key="/abs/path/project",
  program="codex-cli",
  model="YOUR_MODEL",
  name="GreenCastle",        # Optional, auto-generates if omitted
  task_description="Auth work"
)
```

**Agent naming rules:**
- MUST be adjective+noun: GreenCastle, BlueLake, RedBear
- NOT descriptive: BackendHarmonizer, DatabaseMigrator (invalid)
- Best practice: Omit `name` for auto-generation

**Returns:** `{id, name, program, model, task_description, inception_ts, last_active_ts}`

### whois

Get agent profile with recent commits.

```
whois(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  include_recent_commits=true,
  commit_limit=5
)
```

### create_agent_identity

Always create new unique agent (never updates existing).

```
create_agent_identity(
  project_key="/abs/path/project",
  program="codex-cli",
  model="YOUR_MODEL",
  name_hint="GreenCastle"    # Optional
)
```

---

## Messaging

### send_message

Send message to one or more recipients.

```
send_message(
  project_key="/abs/path/project",
  sender_name="GreenCastle",
  to=["BlueLake"],
  subject="API review needed",
  body_md="Please check the auth endpoints...",
  cc=["RedBear"],            # Optional
  bcc=["Overseer"],          # Optional
  thread_id="bd-123",        # Optional, for threading
  importance="normal",       # low|normal|high|urgent
  ack_required=true          # Request acknowledgment
)
```

### reply_message

Reply preserving thread.

```
reply_message(
  project_key="/abs/path/project",
  message_id=1234,
  sender_name="BlueLake",
  body_md="Looks good, one suggestion...",
  to=["GreenCastle"],        # Optional, defaults to original sender
  cc=["RedBear"],            # Optional
  subject_prefix="Re:"       # Default
)
```

### fetch_inbox

Get messages for agent.

```
fetch_inbox(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  limit=20,
  since_ts="2025-01-01T00:00:00Z",  # Optional
  urgent_only=false,
  include_bodies=true
)
```

### mark_message_read

Mark message as read.

```
mark_message_read(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  message_id=1234
)
```

### acknowledge_message

Acknowledge receipt (also marks read).

```
acknowledge_message(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  message_id=1234
)
```

### search_messages

FTS5 full-text search.

```
search_messages(
  project_key="/abs/path/project",
  query='"auth module" AND error',
  limit=20
)
```

### summarize_thread

Extract key points and actions.

```
summarize_thread(
  project_key="/abs/path/project",
  thread_id="bd-123",
  include_examples=true,
  llm_mode=true
)
```

---

## File Reservations

### file_reservation_paths

Reserve files before editing.

```
file_reservation_paths(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  paths=["src/auth/**/*.ts", "src/middleware/auth.ts"],
  ttl_seconds=3600,
  exclusive=true,
  reason="bd-123"
)
```

**Returns:** `{granted: [...], conflicts: [...]}`

Conflicts are advisory — reservations still granted.

### release_file_reservations

Release reservations.

```
release_file_reservations(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  paths=["src/auth/**"],     # Optional, releases all if omitted
  file_reservation_ids=[101] # Optional, by ID
)
```

### renew_file_reservations

Extend TTL.

```
renew_file_reservations(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  extend_seconds=1800
)
```

### force_release_file_reservation

Clear stale reservation from another agent.

```
force_release_file_reservation(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  file_reservation_id=101,
  note="Agent crashed, clearing stale lock",
  notify_previous=true
)
```

---

## Contact Management

### request_contact

Request permission to message another agent.

```
request_contact(
  project_key="/abs/path/project",
  from_agent="GreenCastle",
  to_agent="BlueLake",
  to_project="/abs/path/other",  # Optional, for cross-project
  reason="API coordination",
  ttl_seconds=604800             # 7 days default
)
```

### respond_contact

Accept or deny contact request.

```
respond_contact(
  project_key="/abs/path/project",
  to_agent="BlueLake",
  from_agent="GreenCastle",
  accept=true
)
```

### list_contacts

List contact links for agent.

```
list_contacts(
  project_key="/abs/path/project",
  agent_name="GreenCastle"
)
```

### set_contact_policy

Set contact policy.

```
set_contact_policy(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  policy="auto"  # open|auto|contacts_only|block_all
)
```

---

## Macros

### macro_start_session

One-call bootstrap.

```
macro_start_session(
  human_key="/abs/path/project",
  program="codex-cli",
  model="YOUR_MODEL",
  task_description="Auth refactor",
  file_reservation_paths=["src/auth/**"],
  inbox_limit=10
)
```

**Returns:** `{project, agent, file_reservations, inbox}`

### macro_prepare_thread

Join existing thread with context.

```
macro_prepare_thread(
  project_key="/abs/path/project",
  thread_id="bd-123",
  program="codex-cli",
  model="YOUR_MODEL",
  include_examples=true,
  inbox_limit=10
)
```

### macro_file_reservation_cycle

Reserve, work, auto-release.

```
macro_file_reservation_cycle(
  project_key="/abs/path/project",
  agent_name="GreenCastle",
  paths=["src/auth/**"],
  ttl_seconds=3600,
  auto_release=true
)
```

### macro_contact_handshake

Contact setup with optional auto-accept.

```
macro_contact_handshake(
  project_key="/abs/path/project",
  requester="GreenCastle",
  target="BlueLake",
  auto_accept=true,
  welcome_subject="Coordination request",
  welcome_body="Let's sync on API changes"
)
```

---

## Guard Tools

### install_precommit_guard

Install git pre-commit hook to enforce file reservations.

```
install_precommit_guard(
  project_key="/abs/path/project",
  code_repo_path="/abs/path/project"
)
```

### uninstall_precommit_guard

Remove pre-commit guard.

```
uninstall_precommit_guard(code_repo_path="/abs/path/project")
```

---

## Health

### health_check

Return server readiness status.

```
health_check()
```

**Returns:** `{status: "healthy"}`
