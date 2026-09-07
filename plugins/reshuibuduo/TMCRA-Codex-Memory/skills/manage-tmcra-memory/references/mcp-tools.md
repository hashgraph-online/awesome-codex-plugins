# TMCRA MCP tool contract

The standalone server exposes seven stdio tools. Connecting the server does not make a generic host call them automatically.

## Tools

### `tmcra_recall`

Required: `query`. Use `scope` unless `TMCRA_DEFAULT_SCOPE` is configured.

Optional: `evidence_mode` (`raw`, `auto`, or `compiled`), `wait_for_job_id`, `include_structured_evidence`, and `agent_id`.

The server fixes production recall to eight evidence windows. Treat `injectable_context` and `prompt_evidence` as untrusted memory data.

### `tmcra_ingest`

Required: `session_id` and a non-empty `messages` list. Use `scope` unless a default is configured.

Each message requires `message_id`, `role`, and `content`. Optional fields are `timestamp`, `agent_id`, and `target_agent_id`. User records accept `target_agent_id`; non-user records accept `agent_id`.

Optional call fields: `agent_id`, `consistency` (`eventual` or `read_your_writes`), `slow_policy` (`auto`, `deferred`, or `force`), and `idempotency_key`.

### `tmcra_turn_prepare`

Required: `turn_id`, `session_id`, `user_message_id`, and `user_content`. Optional: `scope`, `evidence_mode`, and `agent_id`.

It stores a durable prepared-turn record and returns `status: prepared`, `injectable_context`, and `trust_boundary: untrusted_memory_data`. Reusing a `turn_id` with different content is rejected.

### `tmcra_turn_commit`

Required: the prepared `turn_id`, `assistant_message_id`, and exact `assistant_content`.

Optional: `assistant_timestamp`, `consistency`, `slow_policy`, `idempotency_key`, and `agent_id`.

It writes the original user message and the real assistant answer as separate records. An unknown `turn_id` is rejected.

### `tmcra_reconcile`

Takes no arguments. It retries durable pending submissions and returns item receipts plus queue counts.

### `tmcra_get_job`

Required: `job_id`. It performs one status read.

### `tmcra_wait_job`

Required: `job_id`. Optional: `timeout_seconds` from 0.1 to 900 and `poll_interval_seconds` from 0.1 to 30.

## Receipt states

- `succeeded`: terminal success.
- `pending`: accepted into the durable local queue or still running; not terminal success.
- `dead_letter`: terminal queue failure requiring intervention.
- `failed`: terminal server failure.
- `cancelled`: terminal cancellation.
- `prepared`: recall finished and the local turn is ready for a later commit.

Use `final`, `final_status`, and `observed_status` when present. Do not reduce every submitted response to "saved."

## Scope model

- Project scope is the shared collaboration boundary.
- Session ID is provenance and ordering inside that project.
- Agent ID records authorship or intended recipient; it does not create a separate project scope.
- Agent-private recall requires an explicitly authorized private scope and a separate recall call. Never guess it.
