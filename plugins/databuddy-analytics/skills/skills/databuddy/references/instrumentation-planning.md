# Databuddy Instrumentation Planning

Use this file when the user asks what to track, how to design metrics, how to attribute server events to browser sessions, or where tracking calls should live.

## Default Output Shape

Do not give a generic event dump. Produce a small plan:

| Question | Metric | Event | Properties | Source | Placement | Verify |
| --- | --- | --- | --- | --- | --- | --- |

Keep the first pass to 3-7 events unless the user asks for a full audit. Each event should answer a product, growth, support, or reliability question.

## Selection Rubric

Choose events by this order:

1. **Decision value**: Will someone act differently if this moves?
2. **Authority**: Backend success/failure beats browser guesses for outcomes.
3. **Funnel value**: Prefer start, key step, completion, and failure events over every interaction.
4. **Segmentability**: Add low-cardinality properties that explain differences.
5. **Stability**: Name product concepts, not component names.
6. **Privacy**: No PII, secrets, raw payloads, raw errors, or long free text.

If only one event is worth adding, choose the authoritative completion event. If there is a flow, add one start event, one completion event, and one failure event before adding intermediate steps.

## Metrics Map

| Goal | Events needed | Useful properties |
| --- | --- | --- |
| Funnel conversion | ordered milestone events | `step`, `source`, `method`, `variant` |
| Activation | first meaningful outcome | `source`, `method`, `template`, `team_size` bucket |
| Feature adoption | feature outcome or repeated use | `feature`, `entrypoint`, `variant`, `status` |
| Reliability | completed and failed backend outcomes | `status`, `duration_ms`, `error_type`, `provider`, `stage` |
| Content quality | feedback or content actions | `page_type`, `source`, `rating`, `category` |
| Experiment impact | exposure plus outcome | `flag_key`, `variant`, `feature`, `status` |
| Retention | an activation event and a meaningful return event (not a pageview), both carrying a profile id from `identify()` or server-side `profileId` | none: the query selects only exact event names, horizon, dates, and an optional `namespace` |

Retention has no dedicated dashboard page. It is the `identified_profile_retention` query: 7- or 30-day return after activation, per daily cohort, counting identified profiles only, so anonymous visitors never enter it. Ask the Databuddy agent or MCP for it with the exact activation and return event names, or query it over REST as shown in [public-surfaces.md](./public-surfaces.md).

Use counts, buckets, booleans, enums, and durations. Avoid exact IDs, emails, names, raw URLs with IDs, exact search text, request bodies, tokens, and stack traces.

## Feature Flag Metrics

Feature flags answer two separate questions:

1. **Who saw what?** Browser single-flag fetches can emit `$flag_evaluated` with `flag`, `value`, `variant`, and `enabled` when the tracker exists. Bulk-prefetched or cached reads may not emit a fresh exposure event, so track an explicit `feature_exposed` event when an experiment needs complete exposure accounting.
2. **Did it matter?** Track the downstream outcome event and include `flag_key` and `variant`.

Plan flag metrics like this:

| Question | Metric | Event | Properties | Source | Placement | Verify |
| --- | --- | --- | --- | --- | --- | --- |
| Did the new flow increase completion? | completion by variant | `project_created` | `flag_key`, `variant`, `source` | server | after durable create succeeds | event has browser IDs and variant |
| Did a rollout create failures? | failure rate by flag state | `job_failed` | `flag_key`, `variant`, `error_type`, `stage` | server | at terminal job failure | no raw error text |
| Did a UI variant improve usage? | outcome count by variant | `report_exported` | `flag_key`, `variant`, `format` | browser or server | when export succeeds | no duplicate outcome event |

Do not track every render of a flagged component. Use one meaningful exposure event and one meaningful outcome event.

## Event Families

- **Intent**: browser event before a user leaves the page, e.g. `signup_started`, `export_clicked`, `integration_opened`.
- **Outcome**: backend event after durable success, e.g. `signup_completed`, `project_created`, `integration_connected`, `report_exported`.
- **Failure**: backend event after expected failure, e.g. `job_failed`, `webhook_processed` with `status: "failed"`.
- **System**: backend or webhook event with `source`, `namespace`, `provider`, `stage`, and `duration_ms`.

Do not track one outcome twice. If browser and server both matter, use different semantics: browser `*_started`, server `*_completed` or `*_failed`.

## Placement Rules

- Browser intent: track before navigation or route transition; call `flush()` if leaving the page.
- Server outcome: track after the database write, external API success, file creation, or job completion is confirmed.
- Server failure: track only useful expected failures; send `status: "failed"` and `error_type`, not raw messages.
- Webhooks and jobs: include `source`, `provider`, `stage`, `status`, and `duration_ms`; include browser attribution IDs only if they were persisted earlier.
- Forms and server actions: pass browser IDs as hidden fields or request body fields; send `anonymousId` and `sessionId` from `getIds()`.
- Cross-domain flows: list the destination domains in `linkDomains` for links and forms, or append `getTrackingParams()` to a URL you build or redirect to; the destination tracker adopts the IDs.
- Known users: in React pass the signed-in user (or `null`) to `DatabuddyProvider`'s `user` prop; elsewhere call `identify(profileId, traits?)` when auth resolves and `reset()` on logout; never put emails or names in event properties or `profileId`. Keep Databuddy browser IDs for web-session attribution; `identify()` links them to the user.

## Attribution Patterns

| Flow | How to preserve attribution |
| --- | --- |
| Browser button -> API route | `getIds()` in the browser; send `{ anonymousId, sessionId }`; server passes them to the Node SDK event |
| Browser form -> server action | populate hidden fields from `getIds()` before submit; server reads the same fields |
| Browser -> another owned domain | list it in `linkDomains`, or add `?${getTrackingParams()}` to a URL you build; install Databuddy on the destination |
| Browser starts async job -> job finishes later | store `anonymousId` and `sessionId` with the job record; job completion event reuses them |
| External webhook after user setup | persist Databuddy IDs during setup; webhook event reuses them when available |
| Pure server/system event | omit session attribution; include `source`, `namespace`, `status`, and useful operational properties |

Attribution can be partial. A server event with only `anonymousId` is still better than no browser linkage; both `anonymousId` and `sessionId` give the strongest session continuity.

## Example Plans

### SaaS Activation

| Question | Metric | Event | Properties | Source | Placement | Verify |
| --- | --- | --- | --- | --- | --- | --- |
| Where do users drop before activation? | step conversion | `signup_started` | `source`, `method` | browser | submit click before auth redirect | event appears before navigation |
| Did signup actually complete? | completion count | `signup_completed` | `method` | server | after user record is created | event has website scope |
| What first value did they reach? | activation rate | `project_created` | `template`, `source` | server | after project insert succeeds | event carries browser IDs |

### Backend Integration Health

| Question | Metric | Event | Properties | Source | Placement | Verify |
| --- | --- | --- | --- | --- | --- | --- |
| Are external callbacks healthy? | success/failure rate | `webhook_processed` | `provider`, `event_type`, `status`, `duration_ms`, `error_type` | server | after webhook handling finishes | failed rows have low-cardinality `error_type` |
| Are background jobs completing? | job failure rate | `job_completed` / `job_failed` | `job_type`, `stage`, `duration_ms` | server | at terminal job state | no raw payloads stored |

## Review Checklist

- Does each event answer a concrete question?
- Is each event placed where the fact becomes true?
- Are start/completion/failure semantics distinct?
- Are attribution IDs passed when a server event belongs to a browser session?
- Are properties low-cardinality and privacy-safe?
- Can Databuddy use this for a funnel, goal, segment, or reliability metric?
