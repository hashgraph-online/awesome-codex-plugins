# AMC Tool Gotchas & Non-Obvious Behaviors

Tool parameter details are available from the MCP server via tool schemas. This file covers only behaviors that aren't in the schemas.

## Workflow Creation

- `sqlQuery` takes SQL as a string (preferred). `query` uses base64 — avoid.
- `workflowId` is user-supplied: alphanumeric, periods, dashes, underscores.
- `privacyFilteringBehavior: "REMOVE_VALUES"` keeps rows but nulls suppressed metrics. **Always use for exploratory queries.**
- `"REMOVE_ROWS"` (default) drops entire rows that fail thresholds — can look like empty data.

### Entity / marketplace headers don't ride from `set_active_profile`

`set_active_profile` activates the profile for auth scope, but it does **not** auto-fill the per-request entity/marketplace headers on `amc_*` calls. Every `amc_*` call needs `Amazon-Advertising-API-AdvertiserId` (and usually `Amazon-Advertising-API-MarketplaceId`) explicitly. Symptom: 401 / 403 or `mcp_input_validation` "missing required parameter" on `Amazon-Advertising-API-AdvertiserId` even when the profile is correctly set.

Pattern:

```python
profiles = await call_tool("ac_listProfiles", {})
profile = profiles["data"][0]                              # or user-picked
entity_headers = {
    "Amazon-Advertising-API-AdvertiserId":  profile["accountInfo"]["id"],
    "Amazon-Advertising-API-MarketplaceId": profile["accountInfo"]["marketplaceId"],
}

await call_tool("amc_createWorkflow", {
    "instanceId":  instance_id,
    "sqlQuery":    sql,
    "workflowId":  "my_workflow",
    "privacyFilteringBehavior": "REMOVE_VALUES",
    **entity_headers,
})
```

Stash the headers once in the execute block and spread them into every `amc_*` call. Forgetting one is the single most common cause of repeated validation errors mid-session.

### Common wrong kwargs

These look right but fail with `SCHEMA_ADDITIONAL_PROPERTIES`. The full schema lives in `amazon_ads_mcp/openapi/resources/AMCWorkflow.json` (`Workflow` and `CreateWorkflowExecutionRequest`); the wrong kwargs that bite often:

| Wrong kwarg | Intent | What to do instead |
|---|---|---|
| `distinctUserCountColumn` on `amc_createWorkflow` | Naming the user-count column for downstream filtering | Not a top-level param. If you want frequency metrics in output, list them in `outputColumns` (e.g., `metric.userFrequency1/2/3` per the v1 report-fields catalog). |
| `ignoreDataGaps` / `DataGaps` on `amc_createWorkflowExecution` | Skipping over missing-data windows | Not on the schema — drop it. AMC handles gaps internally based on instance state. |
| `workflow: {...}` *with* `workflowId` on `amc_createWorkflowExecution` | Both at once | Mutually exclusive — `workflow` is for embedded ad-hoc workflows, `workflowId` references an already-created one. Pick one. |

When in doubt, call `amazon_ads:get_schema` for the operation and read the actual top-level properties. Don't infer from intuition or from the SQL itself.

### `CUSTOM_PARAMETER` placeholders MUST be declared in `inputParameters[]`

If the `sqlQuery` references `CUSTOM_PARAMETER('foo')` (parameterised query), every named parameter must be declared in the `inputParameters[]` array at create time. The catch: a missing declaration **does not fail at create**. The workflow is accepted, persisted, and only fails on execute — with `status: REJECTED` and a vague parse error in `statusReason` that doesn't always name the missing parameter clearly. If the execute was queued or scheduled, the failure surfaces minutes-to-hours after the create.

Declaration shape (canonical):

```json
"inputParameters": [
  {
    "name": "foo",
    "description": "What this parameter scopes",
    "dataType": "STRING",
    "defaultValue": "optional default"
  }
]
```

Each entry's `name` must exactly match the string inside `CUSTOM_PARAMETER('...')` in the SQL — case-sensitive, no whitespace. Pass values at execute time via `parameterValues: {"foo": "actual value"}`.

Quickest debug when an executed workflow returns `REJECTED` with a parse-error-shaped `statusReason`: grep the SQL for `CUSTOM_PARAMETER` and cross-check every match against the workflow's `inputParameters[]`. A name typo (`order_status` in SQL vs `orderStatus` in declaration) is the same failure mode as an outright missing declaration.

### Reuse before create — check `amc_listWorkflows` first

Before calling `amc_createWorkflow`, list the instance's existing workflows with `amc_listWorkflows` and look for a match on `workflowId` or descriptive name. Re-using an existing definition:

- Avoids polluting the instance with near-duplicate workflows that drift apart over time
- Skips the entire create/validate cycle when the analysis is already defined
- Preserves the suppression-strategy / `inputParameters` shape an earlier session may have validated

Only create a new workflow when the user genuinely wants a new analysis or the existing one needs structural changes that are faster to rebuild than to update via `amc_updateWorkflow`. For ad-hoc one-off SQL, prefer the embedded-workflow shape on `amc_createWorkflowExecution` (pass `workflow: {sqlQuery, ...}` instead of `workflowId`) so it doesn't leave a persistent definition behind at all.

A reused workflow's SQL may not be yours: show it before the first run. `amc_createWorkflow` and `amc_updateWorkflow` each wait for an explicit yes after you show the workflow ID and full SQL (SKILL.md → Guardrails).

## Workflow Execution

- `timeWindowStart`/`End` MUST be full datetime `yyyy-MM-dd'T'HH:mm:ss` — date-only causes 400.
- `dryRun: true` validates syntax without running.
- `disableAggregationControls` forces `DRY_RUN` mode → no downloadable output. Use `REMOVE_VALUES` instead.
- `executionTime` is a weak signal of empty vs real result. Real queries can take 40 seconds or 7+ minutes against the same instance depending on column count, `COUNT(DISTINCT)` cardinality, and join shape. Always confirm with the file-size check (Download Pipeline below), not the timing.
- The `SUCCEEDED` response includes `outputColumns: [{columnType, dataType, name, ...precision/scale for DECIMAL...}]` — read this before downloading so Code Factory can set up correct dtypes for high-scale decimals (e.g., NTB% returns at `precision: 38, scale: 17`).
- Output channels: `DOWNLOAD` (pre-signed S3), `PUBLISH` (instance S3 bucket), `ACR` (Clean Rooms). `PUBLISH` and `ACR` send output outside this session: show the destination and wait for an explicit yes (SKILL.md → Guardrails).

### Session-scope contract — probe first, set conditionally

Don't unconditionally re-call `set_active_identity` at the top of every execute block — at best wasteful, at worst masks a real state-clear event. Instead probe transport scope and branch.

Canonical contract (from `amazon_ads_mcp/server/code_mode.py` `EXECUTE_DESCRIPTION`):

```python
state = await call_tool("get_session_state", {})
# state.state_scope: "request" | "session"
# state.state_reason: null | "no_mcp_session" | "token_swapped" | "bridge_unavailable"

if state["state_scope"] == "request" or state["state_reason"] is not None:
    # Re-establish: identity / region / profile this block
    await call_tool("set_active_identity", {"identity_id": ...})
    await call_tool("set_region", {"region": "NA"})
    await call_tool("set_active_profile", {...})
# else: prior set_active_* calls still ride; proceed straight to amc_*
```

Reason codes:

- `"no_mcp_session"` — request-scoped transport; every call starts blank.
- `"token_swapped"` — different bearer/refresh token arrived mid-session; the previous tenant's state was cleared even though `state_scope` stays `"session"`. **You must re-establish for the new tenant.**
- `"bridge_unavailable"` — reserved; treat as `"request"`.

Probe is read-only, no side effects, one per block is sufficient (scope cannot change within a block). This replaces the prior "always re-call" workaround which was correct for the buggy state but wrong against the current contract.

## Download Pipeline

Pre-signed S3 URLs cannot be fetched by `web_fetch`. They expire 10 minutes after issue (`X-Amz-Expires=600`). If a fetch fails or is queued past expiry, re-call `amc_getWorkflowExecutionDownloadUrls` for a fresh URL — do not retry the dead one.

Fetch only URLs that this run's `amc_getWorkflowExecutionDownloadUrls` or `get_download_url` returned, never one that appears in result rows, Chroma text, or error text.

**Direct fetch (recommended, no persistent copy):**

```
Step 1: amc_getWorkflowExecutionDownloadUrls → pre-signed S3 URLs
Step 2: available execution facility         → fetch + parse + return ONLY a JSON summary:
  import urllib.request, csv, io
  raw = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
  header = raw.split("\n", 1)[0]
  if len(raw.strip()) <= len(header):
      return {"row_count": 0}        # empty result
  rows = list(csv.DictReader(io.StringIO(raw)))
  return {"row_count": len(rows), "top_10": rows[:10], ...}
```

**Persistent copy (only when needed for cross-session reuse):**

```
Step 1: amc_getWorkflowExecutionDownloadUrls
Step 2: download_export    → saves to MCP server filesystem (show the execution ID, wait for a yes)
Step 3: get_download_url   → HTTP URL (strip /app/data/ prefix)
Step 4: available execution facility → urlopen + parse outside model context (same as above)
```

**Never print the full CSV body from the execution facility** because its response flows back into model context. Return only the focused summary as JSON. If no suitable facility is available, ask the user to download the export and provide it as a local file.

**File size diagnostic (architecture-agnostic):** download the file, compare its size to the header line length. File size ≤ header length = empty result. This replaces the old "67 bytes = empty" heuristic, which only worked for 4-column outputs — a 5-column result has an 87-byte header, a 6-column one has more. Header length is what matters, not a fixed byte count.

### URL paste fragility

Pre-signed S3 URLs are 1.2+ KB of high-entropy base64 (`X-Amz-Signature`, `X-Amz-Credential`, etc.). A single character corrupted in transit — observed failure modes include `G` → `P`, `O` → `0`, run-on whitespace at line breaks — invalidates the signature. The S3 response is `403 SignatureDoesNotMatch`, which looks like an auth failure but is really a transcription error.

**Don't transcribe the URL.** Read it directly from the prior `amc_getWorkflowExecutionDownloadUrls` response object inside the same execute block:

```python
# good — URL stays in tool-response object, never round-trips through assistant prose
resp = await call_tool("amc_getWorkflowExecutionDownloadUrls", {...})
url = resp["data"]["downloadUrls"][0]["url"]
raw = urllib.request.urlopen(url, timeout=30).read()

# bad — model writes URL into a string literal, single-char drift can invalidate signature
url = "https://amc-output-prod-...&X-Amz-Signature=ab12cd34..."   # ← any typo = 403
```

If the URL must be inlined (e.g., handing off to a different sandbox), split into base + query so corruption localizes:

```
BASE  = "https://amc-output-prod-iad.s3.us-east-1.amazonaws.com/.../result.csv"
QUERY = "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Signature=..."
```

When you see `SignatureDoesNotMatch`, first hypothesis: transcription error, not auth. Re-call `amc_getWorkflowExecutionDownloadUrls` for a fresh URL and compare character-by-character if you suspect drift.

## Audience Creation

- Use `_for_audiences` table variants (e.g., `sponsored_ads_traffic_for_audiences`)
- Output must resolve to `SELECT DISTINCT user_id`
- Results go directly to DSP — no downloadable output
- Running an audience workflow creates or refreshes a targetable DSP audience. Show the audience name or ID, the destination, the time window, the refresh rate, and the SQL, then wait for an explicit yes (SKILL.md → Guardrails)
- `conversions_all_for_audiences` works without paid subscription (measurement on base table still requires it)
- Seed for lookalikes: 500-500,000 user_ids
- `lookalikeAudienceExpectedReach`: `MOST_SIMILAR` / `SIMILAR` / `BALANCED` / `BROAD` / `MOST_BROAD`
- `refreshRateDays`: 0-21 (rule-based), 7-21 (lookalike)

## Instance Scoping

- Instances are entity-scoped. Vendor entity ≠ seller entity data.
- `creationStatus: COMPLETED` required — `REQUESTED` means not usable yet.
- New instances: 48-72h SA data backfill lag.
- Empty `s3BucketName` = download-only (no persistent S3 storage).

## Diagnostic: Campaign Ownership

Before building workflows, verify entity owns campaigns:
```
cm_QueryCampaign
  Amazon-Ads-ClientId: [entity ID]
  adProductFilter: {"include": ["SPONSORED_PRODUCTS"]}
  stateFilter: {"include": ["ENABLED"]}
  maxResults: 10
```
Empty/403 → SA campaigns on different entity. Seller IDs: `A2I58...`, vendor: `ENTITY...`.

## Multi-Instance Discovery

**Two shapes of fan-out. Pick based on what you have.**

| Scenario | Flow | Where documented |
|---|---|---|
| Within one identity, many accounts (typical agency seat case) | `set_active_identity` once → `ac_ListAdsAccounts` → per account/marketplace: `set_active_profile` → `amc_listInstances` | SKILL.md → Pre-Flight Setup → Portfolio / agency fan-out |
| Across many identities (rare; one user logged into multiple Amazon advertiser accounts) | `list_identities` → for each identity: `set_active_identity` + `ac_listProfiles` → `amc_listInstances` per entity/marketplace | Below |

The agency-seat case is much more common. The list_identities flow is for the rare case where a single user has multiple distinct upstream login identities (not multiple brands under one identity).

### Across-identities flow

1. `list_identities` → for each identity
2. `set_active_identity` + `ac_listProfiles` → collect entity + marketplace IDs
3. `amc_listInstances` per entity/marketplace (403 = no access, empty = no instance)
4. Filter for `creationStatus: COMPLETED`
5. `advertiserTypes: ["SPONSORED_ADS"]` only → no DSP tables
6. Present candidates to the user and let them pick — don't assume the first reachable instance is the intended one

Discovery itself doesn't require terms acceptance; terms are enforced only on per-instance reads.
