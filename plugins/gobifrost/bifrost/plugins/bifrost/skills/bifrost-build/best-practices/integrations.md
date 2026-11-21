# Integration Practices

An Integration gives a workflow a credential and a tenant anchor for an external system. Everything the external system returns is visible to that credential, not to the Bifrost caller. The workflow is the only place where caller scoping, field selection, and secret handling can happen.

## Resolve the integration inside the workflow, scoped by context

**Rule:** Call `integrations.get("<name>")` with no `scope=` so it resolves the execution org's mapping (with global defaults as fallback). Use `integration.entity_id` as the tenant anchor (the customer's ID in the external system) and `integration.config` for per-org settings. Pass an explicit `scope=` only in a provider/admin workflow with a value from your own code.

**Why:** The mapping is what ties an org to its tenant in the PSA/RMM/identity provider. Skipping it (hardcoding a tenant ID, taking it as a parameter) is how one customer's workflow reads another customer's data.

```python
from bifrost import context, integrations

integ = await integrations.get("psa")
if integ is None or integ.oauth is None or not integ.oauth.access_token:
    raise RuntimeError(f"PSA is not connected for {context.org_name}; connect it under Integrations")

tenant_id = integ.entity_id          # the caller org's tenant in the PSA
base_url = integ.config["api_url"]
```

Handle `None` (no integration), missing mapping (`entity_id is None`), and missing/expired OAuth as distinct, actionable errors. Use `integ.oauth.refresh()` when a provider reports an expired token.

## Filter to the caller before returning; never return raw payloads

**Rule:** After the external call, restrict results to the caller's organization or contact using identity from `context` and the mapping's `entity_id`, then project to the fields the consumer needs. Return that projection, not `resp.json()`.

**Why:** A PSA `list_tickets` returns every client's tickets the credential can see; an RMM `devices` call returns the whole partner. The App or agent receiving it cannot tell which rows belong to the viewer, and raw payloads carry internal notes, cost fields, and other customers' names.

```python
# Bad: all tenants, every field.
@workflow
async def tickets() -> dict:
    integ = await integrations.get("psa")
    return (await psa_client(integ).get("/tickets")).json()

# Good: tenant-filtered at the source where possible, re-checked locally, projected.
@workflow
async def my_open_tickets(limit: int = 50) -> dict:
    """List the caller's open tickets in the PSA."""
    limit = max(1, min(limit, 200))
    integ = await _require_psa()
    client = psa_client(integ)
    page = await client.list_tickets(client_id=integ.entity_id, contact_email=context.email, status="open", limit=limit)
    items = [
        {"id": t["id"], "subject": t["summary"], "status": t["status"], "updated_at": t["last_update"]}
        for t in page
        if str(t.get("client_id")) == str(integ.entity_id)   # defend against a server-side filter being ignored
    ]
    return {"items": items, "total": len(items)}
```

Filter server-side (API query parameters) *and* re-check locally. Some APIs silently ignore unknown filter parameters; the local check is what makes the leak impossible rather than unlikely. For a customer-facing (`everyone`) workflow, the contact-level filter (`context.email` / a stored external contact ID) is mandatory, not just the tenant filter.

## Decide org vs provider scope deliberately

**Rule:** A workflow for one customer's data runs org-scoped and uses the org's mapping. A workflow that intentionally spans customers (a provider roll-up) is registered for provider/admin roles, iterates `integrations.list_mappings("<name>")`, and labels every row with the org it came from.

**Why:** `list_mappings` returns every org's mapping for a provider caller; mixing those rows into one list without an org label recreates the raw-payload leak one level up.

```python
@workflow
async def provider_open_ticket_counts() -> dict:
    """Per-customer open ticket counts for the provider dashboard."""
    mappings = await integrations.list_mappings("psa") or []
    rows = []
    for m in mappings:
        if not m.organization_id:
            continue
        integ = await integrations.get("psa", scope=m.organization_id)
        count = await psa_client(integ).count_open(client_id=m.entity_id)
        rows.append({"organization_id": m.organization_id, "entity_name": m.entity_name, "open": count})
    return {"items": rows}
```

## Tokens and secrets stay in the workflow

**Rule:** Use `integ.oauth.access_token` and secret config values only to build the HTTP call. Never return them, log them, embed them in a URL you return, or write them to a table or file.

**Why:** Results and logs are visible to the caller. The engine redacts values it handed out through `integrations.get()` and `config.get()`, but a token copied into a table row or a signed-URL query string is outside its reach.

```python
# Bad
logger.info("calling PSA with %s", integ.oauth.access_token)
await tables.insert("debug", {"token": integ.oauth.access_token})

# Good
headers = {"Authorization": f"Bearer {integ.oauth.access_token}"}
logger.info("calling PSA tenant %s", integ.entity_id)
```

## One shared module per outside system

**Rule:** Put the HTTP client for an external system in a module (`modules/<system>/client.py`) that owns base URL, auth header, `httpx.Timeout`, pagination, rate-limit handling, and error translation. Workflows call module methods, never `httpx` directly.

**Why:** Every workflow re-implementing auth and paging drifts; one forgets the timeout, another mis-handles 429, a third returns the raw page. Centralizing also gives one place to filter by tenant.

```python
# modules/psa/client.py
import httpx

class PsaClient:
    def __init__(self, base_url: str, token: str):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(20.0, connect=5.0),
        )

    async def list_tickets(self, *, client_id: str, limit: int, **filters) -> list[dict]:
        items: list[dict] = []
        page = 1
        while len(items) < limit:
            resp = await self._http.get("/tickets", params={"client_id": client_id, "page": page, "page_size": 100, **filters})
            if resp.status_code == 429:
                raise RuntimeError("PSA rate limit reached; retry shortly")
            resp.raise_for_status()
            batch = resp.json().get("tickets", [])
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return items[:limit]
```

## Build requests from parameters, not strings

**Rule:** Pass user values through `params=`/`json=` or the client library's typed arguments. Do not concatenate them into a filter expression, path, or query language the external API interprets.

**Why:** Many PSA/RMM APIs accept filter strings (`$filter`, `search=`). A value containing quotes or operators changes the query. See `security.md`.

## Treat mapping and OAuth mutation as environment administration

**Rule:** `integrations.upsert_mapping()` / `delete_mapping()` change shared instance state for an org. Call them only from an explicit setup/onboarding workflow registered for admin or provider roles, preserve an existing mapping's OAuth binding unless replacement is the intent, and report the change in the handoff.

**Why:** Replacing a mapping can drop the per-org OAuth token the customer consented to; the workflow that "just updates the tenant ID" takes the integration offline.

## Test the failure matrix

**Rule:** Before handoff exercise: no integration, no mapping, missing or expired OAuth, 401/403 from the provider, 429, a page boundary, an empty result, and a result that contains another tenant's rows (assert they are filtered out).

**Why:** The happy path with an admin credential proves nothing about scoping. The leak case is the one that matters and it only shows with multi-tenant test data.

## Checklist

- `integrations.get()` without `scope=`; `entity_id` as tenant anchor; missing states handled.
- Results filtered to tenant and (for end users) contact, server-side and locally; projected fields only.
- Provider roll-ups are role-restricted and label rows by org.
- No token or secret in results, logs, tables, files, or URLs.
- One shared module per outside system: timeouts, paging, 429, error mapping.
- Requests built from parameters, never string-built filters.
- Mapping mutation only in explicit admin workflows.
