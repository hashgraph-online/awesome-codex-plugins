# Admin API Audit

Read this reference for an `audit` or `configure` run that reads a property through the Admin API or changes one setting. It owns the fixed read order, the field each reading produces, the write recipes with their scope and approval tier, and the version boundaries inside the Admin API.

> Korean version: [`admin-api-audit.ko.md`](admin-api-audit.ko.md)

## Contents

- Scope split
- The fixed read order
- Write recipes
- Version boundaries
- Reading a write back

## Scope split

- Reads accept `analytics.readonly` or `analytics.edit`. Use `analytics.readonly` so a mistake cannot write.
- Writes require `analytics.edit` only. The method page states it for each write: "Requires the following OAuth scope: `https://www.googleapis.com/auth/analytics.edit`."
- Property role also gates a write independently of the scope: a scope the credential holds does not grant Editor on the property. Report a role refusal as a role refusal, not as a missing scope.
- Every path below is relative to `https://analyticsadmin.googleapis.com`, and every call carries the property resource name explicitly rather than relying on the first entry of a list.

## The fixed read order

Read in this order and stop the read when the request only needed the first few steps. The order is cheapest and widest first, so an audit can end early without an incomplete account picture.

| Step | Method | What it yields | Finding it supports |
|---|---|---|---|
| 1 | `accountSummaries.list` | Every account and property the credential can see, with property display names and `property` resource names | A property the request assumed exists is absent, or two properties serve the same site |
| 2 | `properties.get` | Industry category, time zone, currency, `createTime`, `parent` account, service level | A time zone that shifts every daily boundary, or a currency that does not match the site's prices |
| 3 | `dataStreams.list` | Each stream, its `type`, and for a web stream `webStreamData.measurementId` and `defaultUri` | A measurement ID on the page that belongs to a different stream, or a missing `defaultUri` |
| 4 | `dataStreams.getEnhancedMeasurementSettings` (v1alpha) | The stream's enhanced measurement switches: `streamEnabled`, `pageChangesEnabled`, `scrollsEnabled`, `outboundClicksEnabled`, `siteSearchEnabled`, `videoEngagementEnabled`, `fileDownloadsEnabled`, `formInteractionsEnabled` | History-based page views (`pageChangesEnabled`) on for an SPA that also sends its own `page_view` |
| 5 | `customDimensions.list`, `customMetrics.list` | Each definition's `parameterName`, scope, `displayName`, and `archived` state | An event parameter collected with no definition, or a definition in `customEvent:` form that the site never sends |
| 6 | `keyEvents.list` | Each key event's `eventName` and `countingMethod` | Marked events with no volume, or conversions that matter left unmarked |
| 7 | `getDataRetentionSettings` | `eventDataRetention` and `resetUserDataOnNewActivity` | Retention at the 2-month default when the reporting question spans a year |
| 8 | `getGoogleSignalsSettings` (v1alpha) | `state` of Google signals | Signals on or off when a demographic or remarketing question depends on it |
| 9 | None - read the GA UI at Admin > Data settings > Data filters | Each filter's name, type, and state (`Testing`, `Active`, `Inactive`), transcribed as read in the UI | An active internal-traffic filter that hides real traffic, or a testing filter that explains a partial gap |
| 10 | `measurementProtocolSecrets.list` | Secret **names and display names only** | Server-side sends with no secret, or a secret whose display name no longer matches its sender |

Rules for the read:

- Step 10 is a policy, not a response shape: `MeasurementProtocolSecret` does carry a `secretValue` field, marked "Output only. The measurement protocol secret value." So read only `name` and `displayName` from each secret, and never echo, log, print, or save `secretValue` - not into the report, not into the chat, not into a commit, and not into a copied response excerpt. When a value must be identified, show at most its first four characters and say the rest is redacted.
- A read that fails at a step is reported at that step with its exact error. Do not skip a step and continue as if the property had no such setting; "could not read" and "not configured" are different findings.
- Quote the field that produced each finding: the `property` resource name for step 1, `webStreamData.measurementId` for step 3, `pageChangesEnabled` from the v1alpha enhanced measurement settings for step 4, `archived` for step 5, and so on. Step 9 has no API field because no API method exists; quote the UI path and the filter row as read. A finding without its field is a guess.
- Step 4 is v1alpha only: the v1beta `dataStreams` method set is `create`, `get`, `list`, `patch`, and `delete`, with no enhanced measurement method, so a v1beta call for it returns 404. That 404 is the expected shape of the call, not a broken stream.

## Write recipes

Every row below carries the `analytics.edit` scope and maps to one approval tier in `rules/safety-gates.md` §1. The tier belongs to the action, so a read-only `audit` that wants one of these becomes a `configure` run for that action.

| Recipe | Method and body | Scope | Approval tier |
|---|---|---|---|
| Create a property | `POST /v1beta/properties` | `analytics.edit` | Named in the request |
| Create a web stream and take its measurement ID | `POST /v1beta/properties/<property_id>/dataStreams` | `analytics.edit` | Named in the request |
| Create a custom dimension or metric | `POST /v1beta/properties/<property_id>/customDimensions` (or `customMetrics`) | `analytics.edit` | Named in the request |
| Archive a custom dimension or metric | `POST /v1beta/properties/<property_id>/customDimensions/<id>:archive` (or `customMetrics`) | `analytics.edit` | Explicit approval |
| Create a key event | `POST /v1beta/properties/<property_id>/keyEvents` | `analytics.edit` | Named in the request |
| Delete a key event | `DELETE /v1beta/properties/<property_id>/keyEvents/<id>` | `analytics.edit` | Explicit approval |
| Lower data retention | `PATCH /v1beta/properties/<property_id>/dataRetentionSettings` | `analytics.edit` | Explicit approval |
| Create a Measurement Protocol secret | `POST /v1beta/properties/<property_id>/dataStreams/<stream_id>/measurementProtocolSecrets` | `analytics.edit` | Named in the request |
| Delete a Measurement Protocol secret | `DELETE /v1beta/properties/<property_id>/dataStreams/<stream_id>/measurementProtocolSecrets/<id>` | `analytics.edit` | Explicit approval |

Each recipe in full:

**Property.** `POST /v1beta/properties` with a `Property` body carrying at least `displayName`, `timeZone`, `currencyCode`, and `parent`. The response is the new property resource name. Creating a property is named in the request, so a request that says "add a property for the new storefront" covers it; a request that says "our analytics is a mess" does not.

**Web stream.** `POST /v1beta/properties/<property_id>/dataStreams` with `type: WEB_DATA_STREAM` and `webStreamData.defaultUri`. The response's `webStreamData.measurementId` is "Output only. Analytics Measurement ID. Example: `G-1A2BCD345E`". Take the ID from the response, never from the request; it does not exist before the call.

**Custom dimension or metric.** `POST /v1beta/properties/<property_id>/customDimensions` with `parameterName`, `displayName`, and `scope` (`EVENT` or `USER`). `scope` is immutable after creation, so a wrong scope is fixed by archiving and creating again, not by a patch. Slot limits still apply: 25 user-scoped, 50 event-scoped, 10 item-scoped, and a deleted slot is reusable only after 48 hours.

**Archive.** `POST .../customDimensions/<id>:archive` retires a definition without freeing its slot immediately and without rewriting history. Explicit approval, because reports that referenced the definition change shape and the archive cannot be undone from the API.

**Key event.** `POST /v1beta/properties/<property_id>/keyEvents` with `eventName` and `countingMethod` (`ONCE_PER_EVENT` or `ONCE_PER_SESSION`). `conversionEvents` is deprecated: the Admin API index says "Deprecated: Use `CreateKeyEvent` instead." Never build a new recipe on the deprecated surface.

**Delete a key event.** `DELETE .../keyEvents/<id>` is explicit approval: reports that counted the event as a conversion change from that point on, and the mark is not restored by re-creating it.

**Data retention.** `PATCH /v1beta/properties/<property_id>/dataRetentionSettings` with `eventDataRetention` (`TWO_MONTHS`, `FOURTEEN_MONTHS`, `TWENTY_SIX_MONTHS`, `THIRTY_EIGHT_MONTHS`, `FIFTY_MONTHS`) and, for the 14-month option and above, `resetUserDataOnNewActivity`. Lowering retention is explicit approval: the deleted user-level data is gone on a monthly cycle and raising the value later does not restore it.

**Measurement Protocol secret.** `POST .../dataStreams/<stream_id>/measurementProtocolSecrets` with `displayName`. The response contains the secret value once, and it is server-side only. Record the display name and the first four characters, never the value. Deletion is explicit approval because a sender that used it stops working.

Tier notes for the two recipes the tier table does not spell out verbatim:

- Secret creation is not in the proceed tier and not in the never tier of `rules/safety-gates.md`. It follows the same named-in-the-request discipline as the other creates, and its value is never printed.
- Secret deletion is listed there under explicit approval by name, so it is asked once with the sender it breaks.

## Version boundaries

| Surface | Version | Note |
|---|---|---|
| `accountSummaries`, `properties`, `dataStreams`, `customDimensions`, `customMetrics`, `keyEvents`, `dataRetentionSettings`, `measurementProtocolSecrets` | v1beta | The surface this reference builds on. `dataStreams` here is the stream resource only: `create`, `get`, `list`, `patch`, `delete` |
| `dataStreams.getEnhancedMeasurementSettings`, `updateEnhancedMeasurementSettings` | v1alpha only | No v1beta equivalent; the v1beta method set has no enhanced measurement member, so a v1beta call for it returns 404 |
| `googleSignalsSettings` (`getGoogleSignalsSettings`, `updateGoogleSignalsSettings`) | v1alpha only | No v1beta equivalent; a v1beta call for it fails |
| `conversionEvents` | Deprecated | Superseded by `keyEvents`; do not use in a new recipe |
| `bigQueryLinks`, `audiences`, `calculatedMetrics`, `channelGroups`, `accessBindings`, `reportingDataAnnotations`, `submitUserDeletion` | v1alpha | Out of scope for this reference; named so a version error is diagnosed correctly |

Google signals being v1alpha means the read at step 8 uses the alpha path and is reported with that caveat; a 404 on the v1beta path is the expected shape of that call, not a broken property. The same holds for the enhanced measurement read at step 4.

## Reading a write back

- After a write, call the matching `get` and quote the field the write changed. A response body from the write method is not the read-back.
- Compare the read-back's `name` with the property and resource named before the write. A concurrent change from another user is not this run's result.
- The read-back proves the setting, not its effect. A new key event, an archived definition, and a lowered retention all take effect for data processed after the change; nothing about history is proven by the read-back.
- A deployed data filter takes 24 to 36 hours to apply. There is no API method for filters, so the state after the change is read again in the UI at Admin > Data settings > Data filters, and the UI can show `Active` while the data still reflects the old state. Say that explicitly.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Every Admin API write requires `analytics.edit`, while reads accept `analytics.readonly` | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams/create> |
| `accountSummaries.list` returns summaries of all accounts accessible by the caller | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| Property creation is `POST /v1beta/properties` | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties/create> |
| A web data stream returns `webStreamData.measurementId`, described as "Output only. Analytics Measurement ID" | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams> |
| `customDimensions`, `customMetrics`, `keyEvents`, `dataRetentionSettings`, and `measurementProtocolSecrets` are v1beta surfaces with create, get, list, patch, archive, and delete verbs | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| `dataStreams.getEnhancedMeasurementSettings` is v1alpha only and returns the enhanced measurement switches, including `pageChangesEnabled` | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.dataStreams/getEnhancedMeasurementSettings> |
| `MeasurementProtocolSecret` carries `secretValue` as "Output only. The measurement protocol secret value", and `get`/`list` return the resource | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams.measurementProtocolSecrets> |
| The v1beta and v1alpha `properties` resource indexes list no `dataFilters` resource, so data filters are read in the GA UI under Admin > Data settings > Data filters | <https://developers.google.com/analytics/devguides/config/admin/v1/rest>, <https://analyticsadmin.googleapis.com/$discovery/rest?version=v1beta> |
| Google signals settings are v1alpha only | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| `conversionEvents` is deprecated in favour of `keyEvents` ("Deprecated: Use `CreateKeyEvent` instead") | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| Custom dimension slots are 25 user-scoped, 50 event-scoped, and 10 item-scoped, freed only 48 hours after deletion | <https://support.google.com/analytics/answer/14240153> |
| Lowering retention deletes older user-level data on a monthly cycle and cannot be restored | <https://support.google.com/analytics/answer/7667196> |
| A data filter's effect is permanent and activation takes 24 to 36 hours | <https://support.google.com/analytics/answer/10104470> |
| Property roles gate writes: Editor for custom dimensions, Marketer or Editor for key events | <https://github.com/googleanalytics/google-analytics-mcp> |

### Evidence grade

`MEASURED` for the scope split, the method paths, the `webStreamData.measurementId` field, the version boundaries (including that the enhanced measurement read is v1alpha only and that no `dataFilters` resource exists), the `secretValue` field on `MeasurementProtocolSecret`, the deprecated `conversionEvents` surface, the slot limits, the retention behaviour, and the filter timing, from the pages above read on 2026-11-08. `LOCAL` for the ten-step read order and the mapping of each reading to a finding; the order is this package's design that walks widest to narrowest so an audit can stop early. The approval tier of every write is taken from `rules/safety-gates.md`, and the two rows it does not name verbatim (secret creation and secret deletion) are called out where they are used rather than silently assigned. The rule to read only `name` and `displayName` from a secret is this package's policy over a field the API does return, not a claim about the response shape.
