# MCP and Auth

Read this reference for a credential question, an API-enablement question, or a decision about the official Google Analytics MCP server. It owns the application-default-credentials setup, the property access grant, the two APIs that must be enabled, the server's install, its read-only default, its full tool list, and the REST fallback when the server is not connected.

> Korean version: [`mcp-and-auth.ko.md`](mcp-and-auth.ko.md)

## Contents

- Credential setup
- Property access
- Enable both APIs
- The MCP server
- Tool list
- Read-only default and write tools
- REST fallback
- Stop conditions

## Credential setup

Application default credentials with both scopes, in one command:

```sh
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/analytics.readonly"
```

- `cloud-platform` is needed for the client library and quota attribution path; `analytics.readonly` is the read scope for both the Data API and the Admin API.
- Add `analytics.edit` to the scope list only when the run will write. A credential with the edit scope and no write in the run is wider than the run needs.
- A service account works through impersonation: `gcloud auth application-default login --impersonate-service-account=SERVICE_ACCOUNT_EMAIL --scopes=...`.
- Set `GOOGLE_CLOUD_PROJECT` so the request is attributed to a cloud project for quota. A missing project is a quota-attribution gap, not an auth failure, and it is reported as such.
- Check presence without printing anything: `[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]`. Never run `echo`, `env`, a config dump, or `gcloud auth print-access-token` to prove a credential exists; the token command writes a bearer token into the shell history and the transcript.

## Property access

- The credential's identity must also be granted access to the property in the Google Analytics UI. "In the Google Analytics UI, grant your user account access to a Google Analytics property."
- A service account is not a property user by default. An identity that authenticates successfully and still sees no property has an access grant missing, not a broken credential.
- The grant and the scope are separate gates. A run with `analytics.readonly` and no property role reads nothing; a run with a property role and no scope is rejected before the property is consulted. Report which one failed.
- Property role decides writes independently: Editor for custom dimensions, Marketer or Editor for key events.

## Enable both APIs

Both APIs must be enabled on the cloud project that owns the credential:

```sh
gcloud services enable analyticsdata.googleapis.com analyticsadmin.googleapis.com
```

- The requirement is the two service names, `analyticsdata.googleapis.com` and `analyticsadmin.googleapis.com`; the `gcloud services enable` line is the ordinary way to turn them on and is shown as the call, not as a documented quotation.
- `analyticsdata.googleapis.com` serves `runReport` and the rest of the Data API; `analyticsadmin.googleapis.com` serves `accountSummaries.list` and the Admin API.
- A report that fails while the Admin API read succeeds means only the data API is enabled, and the reverse means the opposite. Name the disabled API and the step it blocks instead of retrying the call.
- An API-enablement error is a project-level setting. It is not fixed by a new login, a new scope, or a different property.

## The MCP server

Google publishes exactly one official agent tool for this surface: `googleanalytics/google-analytics-mcp`, published on PyPI as `analytics-mcp`.

```sh
pipx run analytics-mcp
```

- Install with `pipx run`; no `uvx` invocation is documented for this server.
- Version history that matters for pinning: 1.0.0 released 2026-11-03, when it graduated from experimental, and 1.1.0 released 2026-11-06, which added the Admin write tools and `minute_ranges` for realtime. A recipe that needs a write tool requires 1.1.0 or later.
- The server is Apache-2.0, Python 3.10 or later, and there is no separate `analytics` CLI from Google. The MCP server is the CLI-equivalent surface.
- Client registration passes the credentials in the environment, for example `-e GOOGLE_APPLICATION_CREDENTIALS=... -e GOOGLE_CLOUD_PROJECT=... -- pipx run analytics-mcp`. The values are environment references, never literals in a committed config.
- Multi-tenant deployments use `--transport http --stateless-http`, or the built-in OAuth 2.1 path with `--oauth` and `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`. The OAuth state is in memory, so that path assumes a single instance.

## Tool list

All thirteen tools, ten read and three write. The write column says what the tool needs beyond a read.

| Tool | Access | What it returns or changes | Extra requirement for a write |
|---|---|---|---|
| `get_account_summaries` | read | Every account and property the credential can see | - |
| `get_property_details` | read | One property's configuration | - |
| `list_google_ads_links` | read | The property's Google Ads links | - |
| `list_property_annotations` | read | Data annotations on the property | - |
| `list_key_events` | read | The property's key events | - |
| `run_report` | read | A Data API report | - |
| `run_funnel_report` | read | A funnel report, which is the v1alpha surface behind it | - |
| `run_conversions_report` | read | A conversions report, including Google Ads cost and attribution rows where linked | - |
| `get_custom_dimensions_and_metrics` | read | The property's custom definitions | - |
| `run_realtime_report` | read | A realtime report over the last 30 minutes | - |
| `create_property_annotation` | write | Creates a data annotation | `--allow-write` and `analytics.edit` |
| `create_custom_dimension` | write | Creates a custom dimension | `--allow-write` and `analytics.edit`, plus the Editor role |
| `create_key_event` | write | Marks an event as a key event | `--allow-write` and `analytics.edit`, plus the Marketer or Editor role |

- The three write tools are the only ones that change a property. Their existence does not lower a gate: creating a custom dimension is still named in the request, and anything in the explicit-approval tier of `rules/safety-gates.md` has no MCP tool at all, so it stays a REST call behind approval.
- `run_funnel_report` carries the alpha caveat of the method it wraps. On a property whose report must be reproducible, prefer `run_report` over `eventName`.
- `run_conversions_report` returns Google Ads cost and attribution rows only for a linked account. An empty result on an unlinked property is not a conversion finding.

## Read-only default and write tools

- The server is read-only by default: `ANALYTICS_MCP_ALLOW_WRITE` / `--allow-write` defaults to `false`, and the flag is described as "Enable tools that create or modify Google Analytics resources."
- A connected server with the write tools absent from its tool list is the default state, not a broken install. Say that the tool is unavailable because write mode is off, not that the server lacks it.
- Turning write mode on is a decision for the run that needs it. It does not by itself authorise a write; the approval tier still applies per action.
- When write mode is on and a write tool is called, the credential needs `analytics.edit` in addition. A `PERMISSION_DENIED` from a write tool with write mode on is a scope or role finding, and the reference names which one.

## REST fallback

When the MCP server is not connected, the same work goes over the REST API with the ADC bearer token:

```sh
curl -sS -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://analyticsdata.googleapis.com/v1beta/properties/<property_id>:runReport" \
  -H "Content-Type: application/json" \
  -d '{"dateRanges":[{"startDate":"2026-10-01","endDate":"2026-10-31"}],"dimensions":[{"name":"sessionDefaultChannelGroup"}],"metrics":[{"name":"sessions"}],"limit":10,"returnPropertyQuota":true}'
```

- The fallback is the same method surface and the same quota; the MCP server is a wrapper, not a second API. A quota error is identical on both paths.
- Do not print the token. The `$(gcloud auth application-default print-access-token)` substitution above is evaluated inside the request and never echoed; a run that needs to show something shows that a token was used, not its characters.
- Prefer the MCP read tools when the server is connected, because they carry the property and account context; use REST when the question needs a method the server does not expose, such as `checkCompatibility`, `getMetadata`, or any write outside the three write tools.
- The REST path needs the same property access grant and the same API enablement. A fallback does not bypass either.

## Stop conditions

Stop the step and report, rather than working around it, when:

- no credential is present: `GOOGLE_APPLICATION_CREDENTIALS` unset and no ADC file. Name the exact `gcloud auth application-default login` command with its scopes and stop.
- the credential exists but the property is not visible: report the missing property grant, name the property ID the run expected, and stop. Never create a property or a grant to continue.
- a scope or an API is missing: name the scope or the `*.googleapis.com` service and the step it blocks, then stop. Never re-run the same call hoping the error clears.
- the MCP write tool is absent: report that write mode is off and that the action needs `--allow-write` plus approval, then stop that action.
- the identity belongs to a service account with no property role: report the role gap by name and stop.

Never print an access token, a refresh token, a service-account key, or a Measurement Protocol secret into the chat, the report, or a commit. When a value must be identified, show at most its first four characters and say the rest is redacted.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| ADC login with `cloud-platform` and `analytics.readonly` in one command, and the property access grant in the GA UI | <https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart> |
| Both `analyticsdata.googleapis.com` and `analyticsadmin.googleapis.com` must be enabled | <https://github.com/googleanalytics/google-analytics-mcp> |
| The MCP server installs with `pipx run analytics-mcp`, is Apache-2.0 and Python 3.10+, and takes ADC through `GOOGLE_APPLICATION_CREDENTIALS` | <https://github.com/googleanalytics/google-analytics-mcp> |
| `analytics-mcp` 1.0.0 published 2026-11-03 and 1.1.0 published 2026-11-06, the latter adding Admin write tools and `minute_ranges` | <https://pypi.org/project/analytics-mcp/>, <https://api.github.com/repos/googleanalytics/google-analytics-mcp/releases> |
| The thirteen tools: ten read and `create_property_annotation`, `create_custom_dimension`, `create_key_event` as write | <https://github.com/googleanalytics/google-analytics-mcp> |
| Write mode is off by default through `ANALYTICS_MCP_ALLOW_WRITE` / `--allow-write`, described as "Enable tools that create or modify Google Analytics resources" | <https://github.com/googleanalytics/google-analytics-mcp> |
| Writes need `analytics.edit`, with Editor for custom dimensions and Marketer or Editor for key events | <https://github.com/googleanalytics/google-analytics-mcp> |
| Service-account impersonation variant of the ADC login | <https://github.com/googleanalytics/google-analytics-mcp> |
| `GOOGLE_CLOUD_PROJECT` attributes requests to a cloud project for quota | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| Multi-tenant transports via `--transport http --stateless-http` and the OAuth 2.1 path with in-memory state | <https://github.com/googleanalytics/google-analytics-mcp> |

### Evidence grade

`MEASURED` for the ADC command and its scopes, the two API service names, the install command, the version dates, the thirteen tool names and their read/write split, the read-only default and its flag, the property-role requirements, and the impersonation and multi-tenant options, from the pages above read on 2026-11-08. `LOCAL` for the REST fallback shape, the rule that a write tool's presence does not lower an approval gate, and the stop conditions; those are this package's policy over the measured surface. The token-cost and quota behaviour of an MCP call is the Data API's own, not a separate limit, and no source read gives a per-tool cost.
