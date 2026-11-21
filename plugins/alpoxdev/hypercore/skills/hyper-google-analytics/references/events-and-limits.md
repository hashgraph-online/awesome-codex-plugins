# Events and Limits

Read this reference for an event-design question, an ecommerce question, or a limit that a finding depends on. It owns the event categories, the recommended and ecommerce events, the published limits, the naming rules, and the key-event figures.

> Korean version: [`events-and-limits.ko.md`](events-and-limits.ko.md)

## Contents

- Event categories
- Recommended events
- Ecommerce events
- Limits
- Naming and reserved prefixes
- Key events

## Event categories

| Category | Where it comes from | Examples |
|---|---|---|
| Automatically collected | Collected by default once the Google Analytics tag is set up | `first_visit`, `session_start`, `user_engagement` |
| Enhanced measurement | Collected when the switch is on in Analytics | `page_view`, `scroll`, `click`, `view_search_results`, `video_*`, `file_download`, `form_start`, `form_submit` |
| Recommended | A standardized name for a business vertical | `login`, `sign_up`, `purchase`, `generate_lead` |
| Custom | A name the implementer defines | anything not in the lists above |

- Prefer a recommended name over a custom one. Recommended names activate the built-in reports; a custom name only fills a custom dimension.
- Custom event names are case-sensitive, must start with a letter, and may use only letters, numbers, and underscores.
- An event call placed above the tag snippet is dropped. Google "won't process data from events that you place above the Google tag snippet."

## Recommended events

Recommended events are grouped as all properties, online sales, lead generation, and games. The lead-generation set (`qualify_lead`, `working_lead`, `close_convert_lead`, `close_unconvert_lead`, `disqualify_lead`) belongs to the lead reports.

- Use the documented parameter names. A recommended event with a renamed parameter does not populate the report that expects it.
- A recommended event is a name and a schema, not a guarantee that the property has the report enabled.

## Ecommerce events

The funnel order to check in an audit is `view_item_list`, `select_item`, `view_item`, `add_to_cart` or `add_to_wishlist`, `view_cart`, `begin_checkout`, `add_shipping_info`, `add_payment_info`, `purchase`, `refund`.

Two parameters decide whether a purchase is usable:

- `transaction_id` is required for `purchase` and "helps you avoid getting duplicate events for a purchase". A `purchase` without it can double-count a retried call.
- `currency` is a "3-letter ISO 4217 format" value. A missing or invalid currency still records the event count but keeps it out of Google Ads, so a silently broken revenue metric looks like a working one in Analytics.
- `value` is "the sum of `(price * quantity)` for all items", excluding shipping and tax.
- The `items` array holds up to 200 elements; each needs `item_id` or `item_name`, and `quantity` "defaults to `1`".
- `purchase` replaced `ecommerce_purchase`, and `refund` replaced `ecommerce_refund`. A legacy name is a finding.
- `in_app_purchase` is collected automatically on app streams; sending it manually duplicates the event.

Item-level custom parameters carry a documented conflict:

| Path | Item custom parameters |
|---|---|
| Tag (gtag.js and GTM) | 27 |
| Measurement Protocol | 10 |

Do not resolve this by picking one number. Record which path the site uses and keep the lower figure as the safe ceiling when a payload must work through both.

## Limits

Standard property, per the collection-limits page:

| Item | Limit |
|---|---|
| Event name | 40 characters; a longer name marked as a key event loses its `_c` suffix and stops being reported as one |
| Event parameters per event | 25 |
| Parameter name | 40 characters |
| Parameter value | 100 characters, except `page_title` 300, `page_referrer` 420, `page_location` 1,000 |
| User properties | 25 per property; names 24 characters, values 36 characters |
| User-ID | 256 characters |
| Distinct events | 500 per app user per day; web is unlimited |
| Sessions | 2,000 per user per day |
| Key events | 10,000 per user per day |
| Events | 100,000 per user per day |
| Event-scoped custom dimensions | 50 |
| User-scoped custom dimensions | 25 |
| Item-scoped custom dimensions | 10 |
| Custom metrics | 50 |
| Calculated metrics | 5 |
| Key events per property | 30 |

- Google Analytics "doesn't log events, event parameters, and user properties that exceed the following limits", so the 26th parameter is not truncated, it is absent. An event that silently loses a parameter is a real finding even when the event count still rises.
- Deleting a custom dimension frees its slot only after 48 hours.
- Analytics 360 raises these: 100 parameters per event, 100 user properties, 500-character parameter values, 50 key events. Read the property's edition before quoting a limit.

## Naming and reserved prefixes

Reserved prefixes that a custom name must not use: `_`, `firebase_`, `ga_`, `google_`, and `gtag.`. Web properties also reserve `query_id`.

- Reserved Measurement Protocol names include `session_start`, `first_visit`, `user_engagement`, and `error`; `screen_view`, `ad_impression`, and `in_app_purchase` are app-only.
- A name that starts with a reserved prefix is rejected or rewritten, so it never reaches the report as written. Report the intended name and the reserved rule it broke.

## Key events

- "Conversions" were renamed "key events" on March 27, 2024. A document or a code comment that still calls them conversions predates the rename; the report should use the current name and may note the old one once.
- "Conversion" now means an action shared with an advertising product, so the two words are not interchangeable in a GA4 finding.
- A standard property allows 30 key events; Analytics 360 allows 50.
- `purchase`, `first_open`, `in_app_purchase`, `app_store_subscription_convert`, and `app_store_subscription_renew` are marked automatically.
- Marking an event as a key event "affects reports from time of creation. It doesn't change historic data", and the change can take up to 24 hours. Never report a read-back as proof that history changed.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| The four event categories and the rule that events above the snippet are dropped | <https://developers.google.com/analytics/devguides/collection/ga4/events> |
| Recommended events are grouped by all properties, online sales, lead generation, and games | <https://support.google.com/analytics/answer/9267735> |
| `purchase` requires `transaction_id`, `currency` is ISO 4217, `value` excludes shipping and tax, and `items` holds up to 200 elements | <https://developers.google.com/analytics/devguides/collection/ga4/reference/events>, <https://developers.google.com/analytics/devguides/collection/ga4/ecommerce> |
| Item custom parameters are 27 on the tag and 10 in the Measurement Protocol | <https://support.google.com/analytics/answer/9267744>, <https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events> |
| Event name 40 characters, 25 parameters, 100-character values with `page_title` 300, `page_referrer` 420, `page_location` 1,000, and 25 user properties | <https://support.google.com/analytics/answer/9267744> |
| Custom dimension slots are 25 user-scoped, 50 event-scoped, and 10 item-scoped, freed 48 hours after deletion | <https://support.google.com/analytics/answer/14240153> |
| Reserved prefixes `_`, `firebase_`, `ga_`, `google_`, `gtag.`, plus `query_id` on web | <https://support.google.com/analytics/answer/13316687> |
| Conversions were renamed key events on March 27, 2024 | <https://support.google.com/analytics/answer/13420269> |
| 30 key events on a standard property, 50 on 360, five auto-marked events, and the change not affecting history | <https://support.google.com/analytics/answer/13128484> |
| 360 raises parameters to 100, user properties to 100, values to 500 characters, and key events to 50 | <https://support.google.com/analytics/answer/11202874> |

### Evidence grade

`MEASURED` for every limit, parameter name, prefix, date, and quote, from the pages above read on 2026-11-08. `LOCAL` for the rule that a payload spanning both paths keeps the lower item-parameter ceiling, and for the audit funnel order used as a checklist; the funnel order comes from the ecommerce page while the ceiling rule is this package's conservative choice. The item-parameter conflict is reported as a conflict because both official pages are current.
