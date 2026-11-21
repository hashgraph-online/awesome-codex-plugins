# Python SDK Decisions

Inside a running workflow, import scoped SDK singletons from `bifrost`. Use this file to choose the right namespace and avoid return-shape/security traps. Read `../generated/python-sdk-signatures.md` before writing an unfamiliar call.

## Data and files

### `tables`

Use for JSON-document table data. Returned `DocumentData` and `DocumentList` are models, not dictionaries:

```python
from bifrost import tables

created = await tables.insert("clients", {"name": "Acme"})
result = await tables.query("clients", where={"name": "Acme"})

client_id = created.id
names = [row.data.get("name") for row in result.documents]
```

Use attribute access. In Python, `tables.delete()` deletes a table; use `delete_document()` for a row. Read `tables.md` before mutations.

### `files`

Use for managed text/binary data and signed transfers:

```python
from bifrost import files

await files.write("reports/status.txt", "ready", location="documents")
content = await files.read("reports/status.txt", location="documents")
```

Choose an explicit declared location for Solution runtime files. Read `files.md` for source/runtime and fallback boundaries.

## Environment and integrations

### `config`

Use for environment config values and secrets. `get()` follows the execution's org/global resolution. `set()` and `delete()` mutate shared instance state, including from a Solution workflow; they are not private install storage.

```python
from bifrost import config

endpoint = await config.get("service_url", default="https://example.invalid")
```

Never return secret values to an app or include them in logs.

### `integrations`

Use `integrations.get()` to resolve an Integration's org mapping, config, and OAuth credentials server-side. OAuth is a model with attribute access, not a dictionary.

Use mapping mutation only for an intentional environment-management workflow. Preserve existing OAuth state unless replacement is required and authorized.

## Orchestration

### `workflows`

Execute another registered workflow by portable ref and receive an execution ID:

```python
from bifrost import workflows

execution_id = await workflows.execute(
    "functions/notify.py::send",
    input_data={"ticket_id": 4821},
)
```

Never pass the caller's identity (email, user id, org) as input. The child reads it from `context` (`from bifrost import context`); see `best-practices/security.md`.

Use delayed execution for scheduling, then query/cancel through the same namespace. A nested loose workflow resolved by an open Solution executes in its own loose context; it does not inherit Solution ownership.

### `executions`

Use to inspect the current execution's logs or query other execution records. Avoid polling loops inside a workflow; schedule/compose work through the workflow APIs.

### `events`

Emit a topic for subscribed workflows/agents:

```python
from bifrost import events

result = await events.emit("acme.deal_won", {"deal_id": "d-123"})
```

Treat event payloads as a versioned contract. Topic-triggered execution context carries the event type, data, organization, and receipt time.

## AI surfaces

### `agents`

Use `agents.run()` when workflow orchestration needs to wait for a configured Bifrost agent. The result may be structured data or text according to the agent contract. Use `agents.enqueue()` to return immediately with a run ID, then call `agents.get_run()` when you need its current status or result. Set bounded timeouts for synchronous runs and do not recursively delegate without a stopping condition.

### `ai`

Use the configured model provider for completion, structured output, or streaming. `ai.complete()` uses the profile marked Default unless `profile=` names another reusable profile. Prefer structured output for machine-consumed results and validate it before side effects.

```python
from bifrost import ai

response = await ai.complete(
    prompt="Summarize the incident in three bullets.",
    profile="Summarization",  # Omit to use the platform default profile.
    max_tokens=250,
)
summary = response.content
```

Do not put secrets or unnecessary personal data into prompts. Treat model output as untrusted input before invoking tools or writing records.

### `knowledge`

Store and semantically search namespaced content. Choose stable keys/namespaces, attach useful metadata, and define deletion/update behavior so re-indexing does not create silent duplicates.

## Platform metadata and administration

### `forms`

Read form metadata when workflow behavior depends on the form definition. Do not use it as a substitute for validated workflow parameters.

### `organizations`, `roles`, and `users`

These privileged namespaces manage tenant and identity state. Resolve the target, inspect dependencies/membership, and require explicit authorization before mutations. Organization deletion and broad role reassignment deserve separate impact review.

## Scope rules

- Omit explicit scope to use the current execution context.
- Pass an organization scope only when the SDK method supports it and the caller is authorized.
- Solution context is carried automatically for tables, files, and workflow resolution.
- Pass `solution=` (install UUID or slug) to reach another install per-call on `workflows.execute`, `tables.query`/`get`/`insert`, `files.read`, and `events.emit`; it resolves inside the resolved org scope and the target's `allow_inbound_access` gate decides. Read `solution-resource-access.md` before targeting cross-install.
- `allow_outbound_access` changes fallback for modules, workflows, tables, and files—not configs, integrations, or knowledge.
- SDK access never bypasses policies, roles, org boundaries, or external-user restrictions.

## Verification

Check the generated signature before every unfamiliar call. Test return shapes, missing resources, access denial, downstream failure, timeout, and empty results. Keep platform-administration and secret mutations visible in the plan and final handoff.
