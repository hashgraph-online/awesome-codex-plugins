# Workflow Practices

Read `security.md` first; this file assumes identity, scope, and input rules are already applied. `references/workflows.md` covers decorators, registration, and testing; `references/python-sdk.md` covers return shapes.

## Keep the decorated function thin

**Rule:** A `@workflow` validates input, calls module functions, and shapes the result. Domain and integration logic lives in an importable module with its own tests.

**Why:** Workflows run only inside the engine; modules run under plain `pytest`. Logic buried in the workflow body cannot be unit-tested, reused by a second workflow, or shared with an agent tool.

```python
# workflows/tickets.py
from bifrost import context, workflow
from modules.psa import tickets as psa_tickets

@workflow(category="Service Desk", tags=["psa", "tickets"])
async def my_open_tickets(limit: int = 50) -> dict:
    """List the caller's open tickets."""
    limit = max(1, min(limit, 200))
    items = await psa_tickets.list_open_for_contact(context.email, limit=limit)
    return {"items": [t.to_public_dict() for t in items], "total": len(items)}
```

## Name and describe for the audit trail

**Rule:** Name workflows `verb_object` (`issue_credit`, `sync_devices`, `my_open_tickets`), give them a first-line docstring that states the effect, set `category`, and keep the name stable. Tools exposed to agents use `{context}_{action}` (see `references/workflows.md`).

**Why:** The execution list, ROI reports, and agent tool search show the name and description; `run`, `handler`, and `process` tell an operator nothing six months later. Renaming re-registers under a new UUID unless done with `workflows replace`.

## Return a shaped, documented result

**Rule:** Return a JSON-serializable dict with a stable shape: `{"items": [...], "total": n}` for lists, explicit fields for single objects, and no raw third-party payloads. Document the shape in the docstring. The result is the contract for Apps, forms, and agents.

**Why:** Apps type the result (`useWorkflowQuery<{items: Ticket[]}>`); a shape that changes with the upstream API breaks every consumer silently. Raw payloads also carry fields nobody reviewed for exposure (`integrations.md`).

```python
# Bad
return resp.json()

# Good
return {
    "items": [{"id": t["id"], "subject": t["summary"], "status": t["status"]} for t in page],
    "total": total,
}
```

## Fail loudly with an actionable message

**Rule:** Raise on failure. Do not catch an exception, log it, and return a success-shaped result. Convert expected upstream failures into `ValueError`/`RuntimeError` messages that say what failed and what the user can do, without secrets or stack traces.

**Why:** A swallowed error becomes a `Success` execution with empty data. Apps render an empty state, nobody is paged, and the bug is discovered weeks later from a customer.

```python
# Bad
try:
    rows = await psa.list_tickets()
except Exception:
    logger.exception("psa failed")
    rows = []

# Good
resp = await client.get("/tickets", timeout=20)
if resp.status_code == 429:
    raise RuntimeError("PSA rate limit reached; retry in a minute")
resp.raise_for_status()
```

Partial failure in a batch is a result, not an exception: return `{"processed": n, "failed": [{"id": ..., "reason": ...}]}` and let the caller decide. Use standard `logging.getLogger(__name__)`; the engine captures it into the execution log stream. Do not `print` secrets or whole payloads.

## Bound time: deadlines, HTTP timeouts, and no polling loops

**Rule:** Every external call sets an explicit timeout. Long work checks `context.workflow_deadline` between steps and stops cleanly before it. Never busy-poll another execution or an external job inside a workflow; use `workflows.execute(..., delay_seconds=...)` to re-enter later, or `agents.enqueue()` / `agents.wait(timeout=...)` for agent runs.

**Why:** The workflow timeout (default 1800 s, set on the row) kills the process; work in flight is lost and nothing records how far it got. An unbounded `httpx` call hangs a worker slot for the full timeout.

```python
import httpx
from datetime import datetime, timedelta, timezone

async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
    for batch in batches:
        if context.workflow_deadline and datetime.now(timezone.utc) > context.workflow_deadline - timedelta(seconds=30):
            await workflows.execute("workflows/sync.py::sync_devices", {"cursor": cursor}, delay_seconds=5)
            return {"status": "continued", "cursor": cursor}
        ...
```

## Paginate; never load everything

**Rule:** Accept `limit` with a hard ceiling and a cursor; page the upstream API and the table (`tables.query(..., limit=, after_document_id=, skip_count=True)`). Return `total` only when it is cheap or required.

**Why:** `tables.query` defaults to 100 and caps at 1000; an upstream API returns pages. "Fetch all then filter in Python" is the pattern behind most workflow timeouts and memory kills.

```python
result = await tables.query(
    "devices",
    where={"status": {"eq": "active"}},
    order_by="created_at",
    limit=200,
    after_document_id=cursor,
    skip_count=True,
)
next_cursor = result.documents[-1].id if len(result.documents) == 200 else None
```

## Scheduled, webhook, and topic workflows must be idempotent

**Rule:** Assume every triggered run can happen twice (retry, overlapping schedule, duplicate delivery). Key writes on a natural or event identity (`tables.upsert(table, id, data)`, `tables.bulk_upsert`) instead of inserting, and record the processed `context.event.id` when the side effect is not naturally idempotent (sending mail, creating a PSA ticket).

**Why:** Event delivery and schedules retry on failure; an `insert`-based subscriber produces duplicates and a "create ticket" subscriber opens two tickets.

```python
@workflow
async def on_alert() -> dict:
    """Open one PSA ticket per RMM alert."""
    event = context.event
    alert_id = str(event.data.get("alert_id", ""))
    if not alert_id:
        raise ValueError("alert_id missing")
    if await tables.get("processed_alerts", alert_id):
        return {"status": "duplicate", "alert_id": alert_id}
    ticket = await psa.create_ticket_for_alert(event.data)
    await tables.upsert("processed_alerts", alert_id, {"ticket_id": ticket.id, "event_id": event.id})
    return {"status": "created", "ticket_id": ticket.id}
```

For schedules, make the unit of work resumable (store a cursor/high-water mark in a table row) so a re-run continues instead of restarting.

## Validate event payloads like any other input

**Rule:** Read triggered data from `context.event.data` (and `context.event.type`), check presence and type of every field you use, and treat the shape as a versioned contract. Do not depend on legacy flat-parameter mapping of the body.

**Why:** Topic emitters change over time; a subscriber that assumes `data["deal"]["id"]` crashes on the first emitter refactor and the failure only shows in the execution list.

## Emit events with a stable, documented payload

**Rule:** `events.emit("domain.event_name", {...})` carries small, stable, ID-based payloads; subscribers fetch detail. Name topics `domain.past_tense_event`.

**Why:** Payloads are copied into every delivery and execution; large or shape-shifting payloads couple every subscriber to the emitter's internals.

```python
await events.emit("billing.credit_issued", {"credit_id": credit.id, "org_id": context.org_id})
```

## Loop over shared code; start another workflow only for a reason

**Rule:** To reuse logic, import it from a shared module and call it, in a loop when there are many items. Start a separate run with `workflows.execute(ref, input_data)` only when you need what a run gives you. `execute` returns the new run's execution id at once and never its result:

- **Hand off and move on:** a form, app button, or endpoint must return now while long work continues, or the work should happen later (`delay_seconds`, `scheduled_at`).
- **Each item stands alone:** one item's failure, timeout, or memory use must not stop the others, and each item should show up in history on its own so it can be inspected and rerun.
- **Calling something you don't own:** the target is a registered workflow with its own access settings (another Solution's, or a shared Workspace workflow), and you need its access check rather than its source.

When you do start one, pass everything it needs in `input_data`; it is a separate run with its own access check and cannot see the caller's parameters or form inputs.

**Why:** Every run costs a queue round trip, a worker slot, a database row, logs, and a module load, and a caller that needs the result has to poll `workflows.get()` while holding its own slot. A loop over a function in the same run does the same work for a fraction of that, returns its result directly, and keeps one history entry.

```python
# Bad: one run per device, then polling to learn whether they worked.
ids = [await workflows.execute("sync_device", {"device_id": d["id"]}) for d in devices]

# Good: shared code, one run.
from modules.rmm.sync import sync_device

for device in devices:
    await sync_device(client, device["id"])

# Good: hand off long work and return to the user now.
execution_id = await workflows.execute("rebuild_report", {"report_id": report_id})
return {"started": execution_id}
```

## Agent tools: bounded, descriptive, side-effect-honest

**Rule:** A `@tool` has a self-contained description, typed parameters with narrow ranges, and a result sized for a model (summaries, IDs, counts; never megabytes). Tools that mutate state say so in the description and validate `context.is_agent` paths the same as human paths.

**Why:** The agent picks tools by description and calls them with model-generated arguments; vague descriptions cause wrong tools, unbounded results blow the context window and the cost cap.

```python
@tool(category="Service Desk")
async def psa_search_tickets(query: str, limit: int = 10) -> dict:
    """Search the caller's PSA tickets by subject text. Returns up to `limit` (max 25) matches with id, subject, status."""
    limit = max(1, min(limit, 25))
    ...
```

## `ai.complete()` output is input

**Rule:** Use `response_format=` with a Pydantic model for machine-consumed output, validate it, and never pass model output straight into a tool call, a filter, or a record without the same validation applied to user input.

**Why:** The model can be steered by the content it summarizes; a ticket body that says "close all tickets" must not become an action.

## Data providers return options, nothing else

**Rule:** `@data_provider` functions return option lists fast (cacheable, bounded, no writes) and scope options to the caller via `context`.

**Why:** They run on form render for every viewer; a slow or mutating provider blocks the form and repeats the side effect.

## Checklist

- Thin workflow, logic in a tested module.
- `verb_object` name, docstring states effect, category set.
- Shaped result; no raw payload; shape documented.
- Errors raised with actionable text; partial failure returned as data.
- Timeouts on every external call; deadline respected; no polling loops.
- Paginated reads with a ceiling.
- Triggered workflows idempotent and resumable; payload validated.
- Tools bounded and described; model output validated.
