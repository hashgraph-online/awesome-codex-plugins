# Extract Rewst definitions

## Establish the connection

Confirm the Rewst instance/region, authorized parent and customer organizations,
the account's access, and a restricted export location outside source control.
Use an existing dated snapshot as evidence only; refresh it before relying on
current triggers, integration overrides or organization mappings.

Rewst's browser application has used a private GraphQL endpoint authenticated by
an `appSession` cookie. Treat this as an observed browser contract, not a stable
public API. Verify the endpoint, credential type, organization context, query,
variables and response shape in the user's current session. A bearer token or
public API key is not interchangeable with a browser session cookie.

The user signs in normally, including MFA. In the browser's developer tools,
inspect Network requests while opening a read-only inventory page. Filter for
GraphQL, select the actual request, and note the exact HTTPS endpoint and JSON
request body. Inspect the cookie under the browser's Application/Storage panel
when the observed request uses `appSession`. Supply only that cookie's value,
without the `appSession=` prefix or other cookies. The organization ID can usually be
recovered from the selected organization URL or request variables; verify which
organization it represents before extracting customer data.

Keep only the query, operation name and necessary non-secret variables in the
request manifest. Review their literals too: a query can embed a secret without
using a variable. Keep cookies, authorization headers, session storage and full
HAR/cURL captures out of chat, recordings, plans and source control. If browser
automation cannot expose an HttpOnly cookie through its supported API, have the
user enter it directly into the helper's hidden prompt or their secret manager.
Use authorized session access; an access denial is not a reason to bypass MFA or
the application's permissions.

## Reuse a server-side credential when available

For a new installation, prefer the packaged
[Rewst Migration Solution](https://github.com/gobifrost/bifrost/tree/main/examples/rewst-migration).
It includes the app, server-side export workflows, config declarations, private
runtime storage, and a network-free sample. Install from the documented subpath;
then enter values in **Solutions → Rewst Migration → Configuration**:
`rewst_migration_api_url`, `rewst_migration_org_id`, and secret
`rewst_migration_app_session`. These are declarations, not shared credentials.
Do not put the session in a workflow parameter or browser storage. Validate the
connection in Setup, select authorized source organizations, and export through
the app. Keep sample and live results distinct. Current private API compatibility
must be established by the customer's pilot; inspect every coverage gap.

Inspect the selected Bifrost instance's config **metadata**, and the registered
extractor's source/schema, before asking for another credential. Existing
implementations may use `rewst_app_session` and `rewst_org_id`; these are key
conventions, not values or a guarantee that any extractor is installed.

If an authorized extractor already exists, execute it by its inspected workflow
reference. Resolve the session through `await config.get(<selected key>)` inside
the workflow; keep it server-side and return only export references, counts and
coverage. Verify the execution organization and allowed source organizations.
The workflow's access tuple and output file policies must protect the source
data. An organization ID parameter alone is not authorization.

For a new stored session, the user can enter the value in the selected Bifrost
organization's config UI with type `secret`. Scope ordinary organization
identifiers separately as non-secret config. Record only the chosen keys and
owner in the plan. If the existing key is expired, have the user replace that
key; do not create a second ambiguous credential. Do not retrieve a decrypted
session into a workflow result or use a CLI `--value <token>` argument. Follow
`bifrost:build` before implementing or installing an extractor. Installing the
skill alone does not install the Solution or its registered workflows.

## Use the bundled local helper

When no suitable server-side extractor exists, the bundled
`scripts/rewst_graphql_export.py` runs captured **read queries** using Python's standard
library. The local helper accepts the session through a hidden prompt or a named
environment variable supplied by the user's secret manager. It does not fetch
or decrypt a Bifrost config. A secret-manager reference belongs in a private
runtime configuration; its resolved value must not appear in shell arguments.

Build the credential-free request manifest from current browser requests. Start
with one bounded request to validate the cookie and source scope, then build the
full capture. Consult the helper's `--help` for its exact arguments.

Example manifest shape (replace the illustrative query and organization value
with the current browser request; this is not a verified Rewst schema):

```json
{
  "version": 1,
  "requests": [
    {
      "name": "workflow-inventory",
      "query": "query Inventory($orgId: ID!, $limit: Int, $offset: Int) { workflows(where: {orgId: $orgId}, limit: $limit, offset: $offset) { id name } }",
      "operation_name": "Inventory",
      "variables": {"orgId": "SELECTED_ORGANIZATION_ID"},
      "result_path": "data.workflows",
      "pagination": {
        "limit_variable": "limit",
        "offset_variable": "offset",
        "page_size": 100
      }
    }
  ]
}
```

Run from the installed skill directory, using paths to the user's private
manifest and a **new** output directory:

```bash
python3 scripts/rewst_graphql_export.py \
  --endpoint https://api.rewst.io/graphql \
  --manifest /private/migration/requests.json \
  --output /private/migration/capture-01
```

The example endpoint is the historical default, not a region selector. Replace
it with the endpoint verified in the user's browser. Supply the cookie directly
to the hidden prompt. For secret-manager execution, add
`--token-env REWST_APP_SESSION` and have the manager inject that named variable
into the child process. Never put the cookie literal in a command or request
manifest. Set `--timeout` and `--retries` to bound read attempts; the default
request timeout is 20 seconds with two retries for retryable failures.

Requests can include non-secret `org_references` metadata. Result paths use dot
notation, such as `data.workflows`. Unpaginated requests omit `pagination`;
paginated requests must select a list and declare the actual limit/offset
variable names. Add `operation_name` when the captured body uses `operationName`.
The helper supports offset pagination; cursor/connection pagination needs an
inspected extractor that follows that API's actual cursor contract. Do not label
a first cursor page complete by omitting pagination from its manifest entry.
Organization metadata labels the capture; it does not enforce authorization or
filter responses. Verify returned organization IDs and inherited-resource scope
against the authorized selection, including when a browser page applies its own
client-side filters.

For each query record its result path, whether it is paginated, the actual limit
and offset variable names, and the expected stable ordering. A browser list
request often returns only a summary: capture the detail request too, and repeat
it for every required object ID. The helper executes explicit manifest requests;
it does not automatically discover child organizations or traverse dependency
IDs. Expand the manifest from recovered IDs, or use an inspected extractor that
implements that traversal.

Prefer stable ordering by an immutable identifier when the API supports it.
Offset pagination over changing data can miss objects even without duplicates.
Use an agreed source change freeze or repeat and reconcile the ID/version
inventory, recording changes and gaps before accepting the capture as a baseline.

Validate that an unpaginated endpoint returns the complete selected resource;
label it bounded or unknown otherwise. An exhausted list query is complete only
for its selected fields, filters, organization and resource class. A successful
workflow metadata export does not establish full task-body or integration
coverage.

The helper creates a new output directory with mode `0700` and files with mode
`0600` on POSIX systems, writes selected response data and a checksummed capture
manifest, and reports collection failures without printing response bodies. On
Windows, choose a location whose ACL grants access only to the intended user;
POSIX mode bits do not establish Windows ACL protection. Output remains sensitive: definitions, variables and
execution history may contain credentials or personal data. Do not publish raw
captures or assume that filesystem permissions replace encrypted storage and
retention controls. A partial export is useful evidence but blocks completeness
claims. On interruption or failure keep the old capture and use a new directory
for the next capture; reconcile their manifests rather than overwriting evidence.

## Cover the whole source

Build a per-organization resource checklist. For every class record the query or
export source, fields recovered, pagination/limits, count, capture time and
status: complete for the stated scope, partial, inaccessible, unsupported, or
verified absent.

| Resource | Details needed beyond a name list |
| --- | --- |
| Workflows | Full task/action definitions, input/output schemas, transitions, Jinja, retry/timeouts, variables, subworkflow references, versions and listeners |
| Triggers | Enabled/disabled state, source, organization, conditions, schedules/timezones, forms, run-as settings, integration overrides and future-org behavior |
| Forms | Field definitions, validation, defaults, visibility, organization variables, option generators and workflow bindings |
| Integrations | Installed packs/bundles, custom actions and schemas, overrides, tenant mappings, auth/scopes and dependency references; credentials handled separately |
| Organizations | Parent/customer relationships, mappings, variable ownership and inheritance/cascade precedence |
| Templates and scripts | Full content, type and nested references, including assets not linked to a workflow |
| Crates | Installed version, managed versus unsynced/cloned/customized components and overrides |
| Apps and access | App Builder pages, workflow/data dependencies, user entry points, roles, permissions and intended external users |
| Operational state | Pending/suspended executions, approvals, scheduled future work, deduplication/correlation records and external SQL/table state |
| History | Bounded representative successes, failures and exceptions with retention and redaction rules; capture history is separate from executing workflows |

Recursively follow subworkflows, option generators, listeners, action IDs,
template/script references and app dependencies. Compare collected IDs against
the resource lists; unresolved IDs and dynamic references remain gaps. Query
parent and authorized customer contexts explicitly so inherited resources and
integration overrides are not lost. Use stable IDs to deduplicate while retaining
each object's source scope and version.

## Handle private API changes

On authentication expiry or 401/403, stop credential use, report only the status,
and ask the user to renew the session through the normal sign-in flow. On HTTP
200 with GraphQL errors, unexpected response paths, missing fields or failed
pagination, retain a partial status and inspect a fresh browser read request.
Do not turn a schema mismatch into an empty inventory or guess new operations.
Use bounded retries for read throttling/transient failures; avoid retrying
authentication or schema errors. Do not replay mutations, workflow execution,
configuration saves, imports or trigger toggles during extraction.

Where the private API cannot recover a resource, use Rewst's supported export
for that resource and reconcile it into the coverage register. Some supported
export procedures create or run workflows: include those effects in the user's
authority before using them. Keep missing custom integration definitions and
unlinked forms visible; neither is implied by a workflow export.

Rewst documents workflow JSON bundles in [Workflows](https://docs.rewst.help/documentation/automations/workflows)
and separate template/script bundles in [Templates and scripts](https://docs.rewst.help/documentation/automations/templates-and-scripts).
Its [instance migration checklist](https://docs.rewst.help/support-and-community/roc-support/migrate-between-rewst-instances)
identifies separately handled integrations, variables, custom integrations and
unlinked forms. That checklist concerns Rewst-to-Rewst migration; it is a coverage
aid, not a Bifrost import specification.

## Produce a usable handoff

Keep raw captures immutable. Generate derived summaries and the dependency graph
separately, with pointers back to source IDs and checksums. Include a final
coverage/gap report and a private secret-reference register. Validate a sample
against the browser's displayed definitions and reconcile inventory counts.
Only then use the recovered definitions to populate the migration plan and test
fixtures. Revoke the temporary session when extraction is complete according to
the user's credential policy.
