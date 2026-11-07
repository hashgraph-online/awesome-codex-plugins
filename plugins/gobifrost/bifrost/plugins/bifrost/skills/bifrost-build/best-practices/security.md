# Security Practices

Apply these rules to every workflow, form, app, agent, and policy; do not treat "internal" or "admin-only" as an exemption.

## Identity comes from the execution context, never from input

**Rule:** Read who is calling from `context`, not from a parameter, form field, header, or app state. The platform sets `context.user_id`, `context.email`, `context.name`, `context.org_id`, `context.org_name`, and `context.is_platform_admin` before user code runs; a parameter is whatever the caller typed.

**Why:** A workflow that takes `email: str` and acts on that mailbox lets any caller act as any other user. Workflow parameters are JSON from the browser; nothing validates that `email` belongs to the caller.

```python
# Bad: the caller chooses whose data to touch.
@workflow
async def my_open_tickets(email: str) -> dict:
    return await psa.list_tickets(contact_email=email)

# Good: the platform says who the caller is.
from bifrost import context, workflow

@workflow
async def my_open_tickets() -> dict:
    """List the caller's open tickets."""
    return await psa.list_tickets(contact_email=context.email)
```

If a workflow legitimately acts on *another* user (an admin tool), take the target as a parameter, name it `target_user_id`, and check `context.is_platform_admin` or a role-based registration before acting. Never let the same parameter double as the actor.

Apps follow the same rule. An App can read the signed-in user for display (`useUser()`), but it must never send that identity back to a workflow as input. The workflow already has it. See `apps.md`.

## Know who the execution context is for each trigger

**Rule:** Before relying on `context.user_id` or `context.org_id`, know which trigger the workflow serves. Different triggers populate the context differently.

| Trigger | `context.user_id` / `email` | `context.org_id` | Flags |
|---|---|---|---|
| App, form, CLI, agent chat | The real user | Workflow's org if org-scoped, else the caller's org | `is_agent=True` for agent tool calls |
| Schedule, webhook, topic subscription | The platform system user | The workflow row's organization | `is_platform_admin=True`; `context.event` populated |
| API-key endpoint (`/api/endpoints/...`) | The platform system user | None (GLOBAL) | `is_function_key=True` |

**Why:** A scheduled or webhook workflow has no human caller. Code that "sends a summary to `context.email`" or "filters to `context.user_id`'s rows" silently does the wrong thing, and the `is_platform_admin=True` context means SDK scope overrides succeed where they would fail for a person.

```python
@workflow
async def nightly_sync() -> dict:
    # Bad: there is no person here; this is the system account.
    await notify(context.email, "sync done")

    # Good: the subject comes from the workflow's own org; recipients from config.
    recipients = await config.get("sync_report_recipients", default=[])
```

Unattended runs (schedules, webhooks, topics, endpoint keys) are moving from the system user to an ordinary per-organization identity account that holds only the roles it is given. Do not write unattended code that depends on `is_platform_admin` being true.

Register a scheduled or webhook workflow in the organization it serves (`bifrost workflows register --org "Org A"`); the org then flows into `context.org_id` and every SDK call. Never read the org from the webhook body.

## Integration results are not scoped to the caller

**Rule:** External systems return everything the integration credential can see. Filter to the caller's organization or contact *inside the workflow* before returning, and return only the fields the consumer needs.

**Why:** A PSA, RMM, or identity provider has no idea who the Bifrost caller is. `list_tickets()` returns every tenant's tickets; passing that to an App or agent leaks across customers. The full rule set with code is in `integrations.md`.

## Least privilege on every entity

**Rule:** Register each workflow, form, app, and agent with the smallest access tuple `(organization, access_level, role_ids)` that its real users need. Defaults: `bifrost workflows register` leaves a workflow at `role_based` with no roles (nobody but admins), which is the correct starting point.

| Access level | Grants | Use when |
|---|---|---|
| `role_based` + `--role-ids` | Members of those roles | Default for anything that mutates or reads non-public data |
| `authenticated` | Every non-external user in scope | Read-only internal tooling where every staff member is an intended user |
| `everyone` | Also external/portal users | Customer-facing portals only; the workflow must then filter by caller (above) |
| `private` (agents only) | The creator | Personal agents |

**Why:** Access is checked at the entity, not per call. An `authenticated` workflow attached to a role-restricted app is still callable by any logged-in user through the API; the app's restriction protects nothing.

```bash
# Bad: broad access "to make the app work".
bifrost workflows register --path workflows/billing.py --function-name issue_credit --access-level authenticated

# Good: the role that owns the action.
bifrost workflows register --path workflows/billing.py --function-name issue_credit \
  --org "Org A" --access-level role_based --role-ids billing_admins
```

Keep the tuple compatible across the chain (app -> workflow -> table policy) and test with a representative non-admin user. Platform-admin success proves nothing because the bypass flag skips the checks.

## Org-scoped by default; global only when one workflow truly serves many orgs

**Rule:** Register workflows, tables, configs, and forms in the organization they serve. Use `--global` only for a workflow that must run for every organization and that reads its org from `context.org_id` on every call.

**Why:** An org-scoped workflow executes in its own org no matter who calls it; a global workflow executes in the *caller's* org. That is the correct behaviour for shared tooling, and the wrong behaviour for a workflow that assumes one tenant's credentials or tables.

```python
# A global workflow must be tenant-agnostic: every SDK call inherits the caller's org.
@workflow
async def device_count() -> dict:
    rmm = await integrations.get("rmm")              # resolved for context.org_id
    rows = await tables.query("devices", limit=1)    # the caller's org's table
    return {"org": context.org_name, "count": rows.total}
```

## Scope overrides are privileged; never derive them from input

**Rule:** Omit `scope=` on SDK calls so the execution's org applies. Pass an explicit `scope=` or call `context.set_scope()` only in a workflow registered for provider/admin use, with a value from your own code or a validated parameter, never from an untrusted field.

**Why:** `resolve_scope()` raises `PermissionError` for a non-bypass caller, but a provider-org member or admin passes. A workflow that does `tables.query("invoices", scope=org_id)` with `org_id` from the request lets any provider user read any tenant.

```python
# Bad: caller-controlled tenant.
@workflow
async def invoices(org_id: str) -> dict:
    return await tables.query("invoices", scope=org_id)

# Good: tenant is the execution's own; cross-org tooling is a separate, role-restricted workflow.
@workflow
async def invoices() -> dict:
    return await tables.query("invoices")
```

Same for `workflows.execute(..., org_id=..., run_as=...)`: the server rejects them for non-admins, so an admin-only workflow that forwards a user-supplied `run_as` is an impersonation hole.

## Validate and bound every input

**Rule:** Treat workflow parameters as untrusted JSON. Enforce type, allowed values, length, and range before the first side effect. Type hints are documentation; the engine only coerces `"5"` to `5` for query-string calls and passes unknown keys through.

**Why:** `limit: int = 50` does not stop `limit=1000000`, `status: str` does not stop a 2 MB string, and a `Literal` hint is never enforced at runtime.

```python
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

class SearchInput(BaseModel):
    status: Literal["open", "closed"] = "open"
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=50, ge=1, le=200)

@workflow
async def search_tickets(status: str = "open", query: str = "", limit: int = 50) -> dict:
    """Search the caller's tickets."""
    try:
        params = SearchInput(status=status, query=query, limit=limit)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e.errors()[0]['msg']}") from e
    ...
```

Reject rather than clamp silently when the value indicates a bug or probe. For forms, the field schema validates shape but not semantics; validate again in the workflow because the workflow is also callable without the form.

## No injection: build queries, filters, and prompts from data, not strings

**Rule:** Pass user values as filter operands, query parameters, and typed arguments. Never interpolate them into an external query language, a shell command, a policy expression, or an LLM system prompt.

**Why:** Table filters and policies are JSON ASTs and cannot be injected through a value, but the moment a workflow builds a PSA OData/SQL-like filter string, a `subprocess` command, or a prompt by concatenation, the value becomes code.

```python
# Bad: filter string built from input.
await psa.get(f"/tickets?filter=contact eq '{email}'")

# Good: parameters stay parameters.
await psa.get("/tickets", params={"contact": email})

# Good: table filter operand, not a hand-built expression.
await tables.query("tickets", where={"contact_email": {"eq": context.email}})
```

For `ai.complete()`, put untrusted text in the user message and treat the model's output as untrusted input before invoking tools or writing records.

## Never build storage paths or table names from user input

**Rule:** Managed-file paths and table names come from your code and immutable IDs. A user-supplied filename is data to store in a row, not a path segment.

**Why:** `files.read(f"uploads/{name}")` with `name="../../other/secret.pdf"` reads another prefix; policy checks run on the resolved path, so a traversal that lands inside an allowed prefix still succeeds. See `data.md` for the UUID-path pattern.

```python
# Bad
await files.write(f"exports/{customer_name}/{filename}", data, location="documents")

# Good: your own layout, your own IDs; the display name lives in the table row.
doc_id = str(uuid4())
await files.write_bytes(f"exports/{context.org_id}/{doc_id}.pdf", data, location="documents")
await tables.insert("exports", {"display_name": filename, "doc_id": doc_id})
```

## Secrets are never returned, logged, or shipped to the browser

**Rule:** Values from `config.get()` on secret keys, `integrations.get().oauth.*`, API keys, and signed URLs stay inside the workflow. Return the result of using them, not the values. Do not put them in log lines, error messages, exceptions, or workflow results, and never read them in App code.

**Why:** Workflow results and logs are visible to the caller and stored on the execution. The engine redacts values registered by `config.get()` and `integrations.get()` from outputs, but it cannot redact a token you fetched yourself with `httpx` or built from parts.

```python
# Bad: token in the result and in the error.
token = integ.oauth.access_token
return {"token": token}
raise RuntimeError(f"PSA call failed with token {token}")

# Good
resp = await client.get(url, headers={"Authorization": f"Bearer {integ.oauth.access_token}"})
if resp.status_code >= 400:
    raise RuntimeError(f"PSA request failed: {resp.status_code}")
```

Browser code has no secret surface. If an App needs an external resource, a workflow fetches it and returns the filtered result or a short-lived `files.get_signed_url(..., expires_in=600)` to a file you wrote.

## Public surfaces get the strictest validation

**Rule:** A workflow exposed as an API-key endpoint, a webhook subscriber, or a form with `access_level: everyone` has no trustworthy caller. Verify webhook signatures through the event source's signing secret, validate every payload field, and never let the payload choose the organization, user, or target record.

**Why:** These run as the system user; a payload field that selects the tenant is a cross-tenant write.

```python
@workflow
async def on_vendor_webhook() -> dict:
    """Handle a vendor status callback."""
    body = context.event.data if context.event else {}
    ticket_id = body.get("ticket_id")
    if not isinstance(ticket_id, str) or len(ticket_id) > 64:
        raise ValueError("ticket_id missing or malformed")
    # The org is the workflow's own org (context.org_id), never body["org"].
```

## Policies are the boundary for direct table/file access

**Rule:** Apps call `useTable`/`tables.*`/`files.*` directly and the only check between the browser and the row is the table or file policy. New tables and locations start with admin-bypass only; write explicit `read`/`create`/`update`/`delete` rules keyed on `{"user": "user_id"}`, `{"user": "organization_id"}`, `has_role`, or a claim before an App ships. Policy shape and claim patterns are in `data.md`.

**Why:** A "convenient" `{"actions": ["read"], "when": null}` rule gives every authenticated user every row.

## Checklist before handoff

- Identity read from `context`, not parameters; trigger type known and handled.
- Integration results filtered to the caller/org before return; raw payloads never returned.
- Access tuple is the minimum; verified with a non-admin user who should pass and one who should fail.
- No `scope=`/`set_scope`/`run_as`/`org_id` sourced from input.
- Inputs validated for type, allowed values, length, range; filters and paths built from code and IDs.
- No secret in result, log, error, or App source.
- Table/file policies written and tested with allowed and denied principals.
