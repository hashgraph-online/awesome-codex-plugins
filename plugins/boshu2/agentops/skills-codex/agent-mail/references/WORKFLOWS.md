# Agent Mail Coordination Patterns

Agent Mail is an optional messaging and file-reservation adapter for an
explicitly coordinated multi-writer run. The caller supplies the actors,
project, thread, paths, and message. Agent Mail does not select work, assign
ownership, decide readiness, validate a candidate, or record completion.

## Start an explicit coordination lane

The caller must provide:

- absolute project path;
- sender and recipient identities;
- stable caller-owned thread ID;
- exact path patterns and reservation TTL;
- the factual message to send.

Example:

```text
macro_start_session(
  human_key="/abs/project",
  program="codex-cli",
  model="caller-selected"
)

file_reservation_paths(
  project_key="/abs/project",
  agent_name="GreenCastle",
  paths=["src/auth/**"],
  ttl_seconds=3600,
  exclusive=true,
  reason="caller-supplied packet auth-surface"
)

send_message(
  project_key="/abs/project",
  sender_name="GreenCastle",
  to=["BlueLake"],
  thread_id="auth-surface",
  subject="[auth-surface] write scope active",
  body_md="Reserved src/auth/** for the supplied packet.",
  ack_required=true
)
```

If a reservation conflicts, report the conflicting paths and holder once.
Do not automatically wait, split the packet, retry, or choose a different
scope. The caller owns that decision.

## Request an independent review

A message can carry a review request, but its acknowledgement or reply is not
an AgentOps verdict. Include exact identity and evidence:

```text
send_message(
  project_key="/abs/project",
  sender_name="GreenCastle",
  to=["BlueLake"],
  thread_id="auth-surface",
  subject="[auth-surface] review request",
  body_md="""
Candidate manifest: sha256:...
Acceptance digest: sha256:...
Changed paths: src/auth/oauth.ts, src/auth/oauth_test.ts
Evidence: go test ./src/auth/...
Please return findings with checked and not-checked scope.
""",
  ack_required=true
)
```

The reviewer may reply with findings and evidence references. Validate remains
the sole owner of `verdict.v2`; Agent Mail never turns a reply into PASS.

## Handoff facts

Use one thread to report facts needed by another explicit actor:

```text
send_message(
  project_key="/abs/project",
  sender_name="GreenCastle",
  to=["BlueLake"],
  thread_id="auth-surface",
  subject="[auth-surface] handoff",
  body_md="""
Candidate manifest: sha256:...
Changed paths: src/auth/oauth.ts, src/auth/oauth_test.ts
Checks: go test ./src/auth/... (exit 0)
Unchecked: external identity provider integration
"""
)
```

A handoff carries no implicit ownership, approval, next action, or delivery
authority. The caller interprets it.

## Release reservations

Release only reservations held by the named actor:

```text
release_file_reservations(
  project_key="/abs/project",
  agent_name="GreenCastle",
  paths=["src/auth/**"]
)
```

Releasing a reservation is coordination cleanup, not work completion.

## Failure reporting

Return exactly the observed adapter result:

- session registration succeeded or failed;
- reservation acquired or conflicted, with paths and holder;
- message ID and recipients, or send error;
- release result.

Do not translate transport errors into retry state, queue state, lifecycle
status, or an andon. Stop after reporting the facts.
