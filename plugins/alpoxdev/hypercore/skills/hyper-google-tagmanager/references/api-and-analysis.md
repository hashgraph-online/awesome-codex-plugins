# API and Analysis

Read this file before any Tag Manager API call, in `analyze`, and when reading a container export. Facts marked `volatile` change with the API; the live discovery document (`https://tagmanager.googleapis.com/$discovery/rest?version=v2`) wins over this snapshot.

## Contents

- 1. Tag Manager API v2
- 2. Write pipeline
- 3. Export format and enum casing
- 4. Tools and MCP servers
- 5. Analysis
- Sources

## 1. Tag Manager API v2

Base URL `https://tagmanager.googleapis.com/tagmanager/v2/`. Resource tree (folders, templates, and built-in variables are workspace-scoped; user permissions are account-scoped):

```text
accounts                                   list, get, update
accounts.user_permissions                  list, get, create, update, delete
accounts.containers                        list, get, create, update, delete, lookup, snippet, move_tag_id, combine (deprecated)
accounts.containers.destinations           list, get, link
accounts.containers.environments           list, get, create, update, delete, reauthorize
accounts.containers.versions               get, live, update, delete, publish, set_latest, undelete
accounts.containers.version_headers        list, latest
accounts.containers.workspaces             list, get, create, update, delete, bulk_update, getStatus, quick_preview, sync, resolve_conflict, create_version
accounts.containers.workspaces.{tags,triggers,variables,folders,templates,built_in_variables,clients,zones,transformations,gtag_config}
```

Useful calls: `GET .../containers/{c}:snippet` (the install snippet), `GET .../versions:live` (the published version), `GET .../version_headers:latest`, `GET /tagmanager/v2/accounts/containers:lookup?tagId=GTM-XXXXXXX`.

OAuth scopes (exactly seven, `https://www.googleapis.com/auth/` prefix):

| Scope | Allows | Use for |
|---|---|---|
| `tagmanager.readonly` | View containers and their items | `audit`, `analyze`, `verify` |
| `tagmanager.edit.containers` | Manage containers and items, not versions or publishing | `configure` drafts; also `versions.set_latest` |
| `tagmanager.edit.containerversions` | Manage versions; `create_version`, `quick_preview` | Version creation (named in the request) |
| `tagmanager.publish` | Publish; `environments.reauthorize` | Approval tier only |
| `tagmanager.delete.containers` | Delete containers and workspaces | Approval tier only |
| `tagmanager.manage.users` | User permissions | Approval tier only |
| `tagmanager.manage.accounts` | Account settings | Approval tier only |

Request the narrowest set for the step. Some third-party servers request all seven by default; say so when the user picks one.

Quotas (`volatile`): 10,000 requests per project per day and 0.25 queries per second per project, enforced as 25 requests per 100 seconds; overage answers HTTP 403. Pace one request every 4 seconds or more, and on `userRateLimitExceeded` or `quotaExceeded` back off `(2^n) + random(0..1000) ms` for n = 0..5. A large container audit through the API is slow; prefer one `versions.live` or export read over listing every item.

Service accounts need to be added as Tag Manager users with a container permission (`read`, `edit`, `approve`, `publish`); creating the key alone grants nothing. Client libraries: Python `googleapiclient.discovery.build('tagmanager', 'v2', credentials=...)`, Node `@googleapis/tagmanager`; both use snake_case method names (`create_version`, `bulk_update`, `quick_preview`). No official CLI exists.

## 2. Write Pipeline

```text
GET   .../workspaces                         find or create a dedicated workspace (standard accounts allow 3 at once)
POST  .../workspaces/{w}/bulk_update         atomic multi-item change; new IDs "new_1", "new_2"
GET   .../workspaces/{w}/status              workspaceChange[] and mergeConflict[]
POST  .../workspaces/{w}:quick_preview       compile check; empty body; read compilerError
POST  .../workspaces/{w}:create_version      {name, notes}; deletes the workspace
POST  .../versions/{v}:publish?fingerprint=  approval tier
```

- `update` is a full replace: send the whole item read with `get`, plus `?fingerprint=<value>` as a query parameter. The fingerprint is optional in the API, and omitting it lets the last writer win silently. A stale fingerprint fails; re-read and redo the change, never resend the same body.
- `compilerError: true` comes back with HTTP 200 from `quick_preview`, `create_version`, and `publish`. Stop on it.
- `bulk_update` responses exclude deleted and system-updated items; re-read the workspace to learn the result.
- `create_version` deletes the source workspace. Never run it on the Default Workspace when other people's edits are in it.
- The API has no confirmations and no undo: rollback is publishing an older version.
- Without API access, write an import JSON (§3 shape) under `.hyper/gtm/<slug>/import.json` and tell the user to import it with **Merge** into a new workspace.

## 3. Export Format and Enum Casing

Admin > Export Container produces:

```json
{"exportFormatVersion": 2,
 "containerVersion": {
   "container": {"publicId": "GTM-XXXXXXX", "usageContext": ["WEB"]},
   "tag": [{"tagId": "101", "name": "GA4 - Event - purchase", "type": "gaawe",
            "parameter": [{"type": "TEMPLATE", "key": "eventName", "value": "purchase"}],
            "firingTriggerId": ["201"], "tagFiringOption": "ONCE_PER_EVENT",
            "consentSettings": {"consentStatus": "NEEDED",
              "consentType": {"type": "LIST", "list": [{"type": "TEMPLATE", "value": "analytics_storage"}]}}}],
   "trigger": [{"triggerId": "201", "name": "CE - purchase", "type": "CUSTOM_EVENT",
                "customEventFilter": [{"type": "EQUALS", "parameter": [
                  {"type": "TEMPLATE", "key": "arg0", "value": "{{_event}}"},
                  {"type": "TEMPLATE", "key": "arg1", "value": "purchase"}]}]}],
   "variable": [], "folder": [], "customTemplate": [], "builtInVariable": []
 }}
```

- Enums appear in two casings: exports and real payloads use `CUSTOM_EVENT`, `HISTORY_CHANGE`, `CONSENT_INIT`, `NOT_SET`, `TEMPLATE`, `EQUALS`; the discovery document shows `customEvent`, `historyChange`, `consentInit`, `notSet`. Compare case-insensitively with underscores removed. `scripts/gtm-container-audit.sh` does.
- Tag types are lower-case in both: `googtag` (Google tag), `gaawe` (GA4 event), `html` (Custom HTML), `ua` (Universal Analytics, dead), `awct` (Ads conversion), `awud` (Ads user-provided data), `gclidw` (Conversion Linker), `sp` (Ads remarketing), `flc` (Floodlight), `cvt_<id>` (custom template). `gaawc` (the old GA4 configuration tag) became `googtag` on 2023-09-05; do not create it.
- Variable types: `v` (Data Layer Variable), `c` (Constant), `jsm` (Custom JavaScript), `u` (URL), `k` (1st-party cookie), `smm` (Lookup table), `remm` (RegEx table).
- Built-in trigger IDs: `2147479553` All Pages, `2147479572` Consent Initialization - All Pages, `2147479573` Initialization - All Pages.
- Variable references appear as `{{Name}}` inside any string.
- Exports can contain customer IDs or tokens inside Custom HTML; quote only what a finding needs.

## 4. Tools and MCP Servers

- As of 2026-11-08 Google publishes no Tag Manager MCP server and no Tag Manager agent skill (`volatile`). The official `googleanalytics/google-analytics-mcp` server covers GA4 only (read tools plus three gated writes), and is the official way to read GA4 data for `analyze`.
- `stape-io/google-tag-manager-mcp-server` (Apache-2.0) is the most used community server: one tool per resource with an `action` field, `bulkUpdate`, `quickPreview`, `createVersion`, fingerprint-required updates. Its hosted endpoint passes container configuration through a third party; the local CLI does not. It requests all seven scopes. Recommend the local CLI and least privilege, and treat its write tools under `rules/safety-gates.md`.
- When an MCP server or API credential is present, use it for reads first; when neither is, ask the user for a container export (Admin > Export Container) and work from the file.

## 5. Analysis

### Container health

Run `scripts/gtm-container-audit.sh --file <export.json>`. It reports counts, tag types, and these findings:

| Code | Rule |
|---|---|
| `UA_TAG` (error) | tag type `ua` |
| `NO_FIRING_TRIGGER` (warn) | no `firingTriggerId` and not a sequencing setup or cleanup tag |
| `DUPLICATE_GOOGLE_TAG` (warn) | two `googtag` tags with the same `tagId` |
| `CUSTOM_HTML_DOCUMENT_WRITE` (warn) | Custom HTML calling `document.write` |
| `HISTORY_CHANGE_PAGEVIEW` (warn) | a used History Change trigger next to a Google tag |
| `CUSTOM_HTML`, `PAUSED_TAG`, `CONSENT_NOT_SET`, `UNUSED_TRIGGER`, `UNUSED_VARIABLE`, `NO_CONSENT_INIT` (info) | as named |

Add by hand when relevant: hard-coded `G-`, `AW-`, or `GTM-` IDs instead of a Constant variable; conversion tags on All Pages; Custom JavaScript variable count (CSP risk); naming and folder hygiene (`references/container-design.md` §7); workspaces against the 3-workspace limit; version names left empty. Container size has no API: read the Size indicator on the Versions page (act above 70% of 300 KB).

### Plan versus container

List each event plan row as present, missing, or different (trigger, parameters, consent), and each container tag as planned or unplanned.

### Destination data

- GA4 realtime: `POST https://analyticsdata.googleapis.com/v1beta/properties/{id}:runRealtimeReport` with dimension `eventName` and metric `eventCount`, scope `analytics.readonly`. Window: the last 30 minutes (60 for GA4 360). Quotas (`volatile`): 200,000 realtime tokens per property per day, 10 concurrent requests. Realtime shows event names, not unregistered parameters.
- GA4 history: `runReport` on `eventName` by `date` for the plan's events; standard data lags 24 to 48 hours; report `samplingMetadatas`, thresholding, and `(other)` rows with the numbers.
- Tag coverage (Google tag > Admin > Tools > Tag coverage) has no API: up to 10,000 pages, 30-day activity, 24-hour lag, false "not tagged" from redirects, trailing slashes, URL case, and low traffic. Use its CSV when the user provides it.
- State the date range, the property, and the data latency next to every number.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Resource tree, methods, `compilerError`, `newWorkspacePath` | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest>, <https://tagmanager.googleapis.com/$discovery/rest?version=v2> |
| OAuth scopes | <https://developers.google.com/tag-platform/tag-manager/api/v2/authorization> |
| Quotas and backoff | <https://developers.google.com/tag-platform/tag-manager/api/v2/limits-quotas>, <https://developers.google.com/tag-platform/tag-manager/api/v2/errors> |
| `bulk_update`, `quick_preview`, `create_version`, `publish` fingerprint | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.workspaces/bulk_update>, <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.versions/publish> |
| `combine` deprecated | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers/combine> |
| Client libraries | <https://developers.google.com/tag-platform/tag-manager/api/v2/libraries> |
| Export shape and upper-case enums | `ContainerVersion` schema in <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.versions>; upper-case enums observed in two public container exports on GitHub, 2026-11-08 |
| GA4 configuration tag became the Google tag | <https://support.google.com/tagmanager/answer/4620708> |
| Workspace limit, import and export | <https://support.google.com/tagmanager/answer/7059647>, <https://support.google.com/tagmanager/answer/6106997> |
| GA4 MCP server tool list | <https://github.com/googleanalytics/google-analytics-mcp> |
| Community GTM MCP server | <https://github.com/stape-io/google-tag-manager-mcp-server> |
| GA4 realtime reports and quotas | <https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-basics>, <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| Tag coverage | <https://support.google.com/tagmanager/answer/12270036> |

### Evidence grade

Official Google API documentation and the live discovery document read 2026-11-08; the export example and the community server were read from their public repositories on that date. Tag and variable type codes come from real exports and are not in Google's prose documentation.
