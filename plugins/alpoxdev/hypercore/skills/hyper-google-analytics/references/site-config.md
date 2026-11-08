# Site Configuration

Read this reference for a CSP entry, a cross-domain question, an internal or developer traffic filter, an unwanted referral, or an enhanced measurement toggle. It owns the minimum CSP directives, the linker, the traffic filters, the referral list, and the enhanced measurement switches.

> Korean version: [`site-config.ko.md`](site-config.ko.md)

## Contents

- CSP minimum
- Cross-domain linker
- Internal and developer traffic
- Unwanted referrals
- Enhanced measurement

## CSP minimum

A GA-only property needs these directives. Anything beyond them belongs to another vendor and is out of scope.

```
Content-Security-Policy:
  script-src-elem https://www.googletagmanager.com 'nonce-{SERVER-GENERATED-NONCE}';
  img-src https://www.googletagmanager.com https://*.google-analytics.com;
  connect-src https://www.googletagmanager.com https://*.google-analytics.com https://*.google.com;
```

- Inline container code needs its own allowance, and "the recommended method is to use a nonce". Write `'nonce-<value>'` into `script-src-elem` and render the same value on the snippet's `nonce` attribute.
- Add `frame-src https://www.googletagmanager.com` when a container renders a frame.
- `'unsafe-eval'` is required only for Custom JavaScript variables, which "will evaluate to `undefined` in the presence of a CSP" without it. Custom Templates are the alternative to relaxing the policy.
- Preview mode needs more hosts: `tagmanager.google.com`, `fonts.googleapis.com`, `ssl.gstatic.com`, `fonts.gstatic.com`, and `data:`. Add them only for the preview environment.
- Removing a directive to make a request pass is not a fix. The finding is the missing directive, and the fix is the narrowest host that satisfies the request.
- A nonce forces dynamic rendering on some frameworks. State that cost before recommending the nonce variant; a hash-based policy is the alternative where the snippet is static.

## Cross-domain linker

- The linker passes the same client and session identifiers between domains through a URL parameter named `_gl`, so both domains must run the same `G-` measurement ID.
- "Linker parameters expire after two minutes." A visitor who lands, waits, and then clicks through arrives undecorated and becomes a new session on the second domain.
- `gtag('set', 'linker', { domains: [...] })` must precede the config call. Options: `accept_incoming` (default true when `domains` is set), `decorate_forms` (default false), and `url_position` (`query` or `fragment`).
- Up to 100 conditions can be listed on one domain setting; the same measurement ID must exist on every domain in the group.
- Failure modes to check: a redirect that strips the query string, a handler that calls `Event.stopPropagation()`, and navigation performed by script. Each drops `_gl` and shows the second domain as a referral.

## Internal and developer traffic

- **Internal traffic** works in two parts: define the rule (IP match, with CIDR or regex support) which appends `traffic_type=internal`, then a data filter whose state is Testing, Active, or Inactive.
- **Developer traffic** is a separate filter that excludes events sent with debug mode on. Use it for the site's own testing rather than folding debug traffic into the internal-traffic rule.
- Limits and effects, in the words the property enforces: up to 10 data filters per property, "effects are permanent" on data collected after activation, and application takes 24 to 36 hours.
- Activating a filter is an approval-tier action. State the property, the filter name, its state change, the 24-to-36-hour wait, and the fact that the effect cannot be undone for data already collected, then wait.
- The Testing state shows the filter's effect without applying it permanently; recommend it first.
- A hostname Include filter blocks events with empty hostnames, such as gtag.js traffic in some setups, and is not applied to Measurement Protocol events. Check the rule's direction before reporting a gap as internal traffic.

## Unwanted referrals

- A data stream accepts up to 50 unwanted referrals.
- Each list entry appends `ignore_referrer=true` to matching sessions, and "setting the `ignore_referrer` parameter to any value results in the same behavior".
- Typical entries: a payment processor that returns the visitor, a sibling domain already covered by the cross-domain group, and a staging host.
- Check for a self-referral before adding a list entry. A subdomain that uses a different cookie domain produces self-referrals, and the fix is the cookie domain or the cross-domain group, not a longer referral list.
- Verify by capturing a session that crosses the boundary and confirming the referral source is not the returning host.

## Enhanced measurement

Seven switches exist on a web data stream, each individually controllable:

| Switch | Event | Trigger |
|---|---|---|
| Page views | `page_view` | Page load, and browser history state changes when the history option is on |
| Scrolls | `scroll` | 90% vertical depth |
| Outbound clicks | `click` | A click to a different domain |
| Site search | `view_search_results` | Query keys `q`, `s`, `search`, `query`, `keyword` |
| Video engagement | `video_start`, `video_progress`, `video_complete` | 10, 25, 50, and 75% |
| File downloads | `file_download` | Extensions including `pdf`, `xlsx?`, `docx?`, `pptx?`, `zip`, `mp4`, `mp3`, `wav` |
| Form interactions | `form_start`, `form_submit` | First field interaction, then a submit |

- `page_view` from page loads cannot be turned off; "you cannot turn off collection". The history option is the part that is switchable, and it is the switch that causes SPA double counting.
- On a single-page app, pick one source: leave both page-load and history page views on and send nothing manually, or turn the history option off and send `page_view` yourself. Never both.
- Enhanced measurement changes need no code; a toggle takes effect for the tag already on the page. After changing one, verify with a fresh request rather than a report.
- Turn off a switch only when the site sends the equivalent event itself, and say which switch moved and why in the report.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| GA-only CSP needs `script-src-elem` for `googletagmanager.com`, `img-src` and `connect-src` for `*.google-analytics.com`, and a nonce for inline container code | <https://developers.google.com/tag-platform/security/guides/csp> |
| `'unsafe-eval'` is required only for Custom JavaScript variables, and preview mode needs extra hosts | <https://developers.google.com/tag-platform/security/guides/csp> |
| The linker passes identifiers through `_gl`, up to 100 conditions, and linker parameters expire after two minutes | <https://developers.google.com/tag-platform/devguides/cross-domain> |
| `linker` options are `accept_incoming`, `decorate_forms`, and `url_position`, and `set` must precede `config` | <https://developers.google.com/tag-platform/devguides/cross-domain> |
| Internal traffic appends `traffic_type`, filters have Testing, Active, and Inactive states, up to 10 per property, permanent effects, and 24 to 36 hours to apply | <https://support.google.com/analytics/answer/10104470> |
| The Developer Traffic filter excludes events sent in debug mode | <https://support.google.com/analytics/answer/13296662> |
| Up to 50 unwanted referrals per stream, and `ignore_referrer` behaves the same for any value | <https://support.google.com/analytics/answer/10327750> |
| Subdomain self-referrals come from a different cookie domain and are fixed by cookie domain or cross-domain settings | <https://support.google.com/analytics/answer/10071811> |
| The seven enhanced measurement switches, their events, and that page-load `page_view` cannot be turned off | <https://support.google.com/analytics/answer/9216061> |
| The history option lives under Page views advanced settings, and turning on both automatic history tracking and a tag-manager history trigger double-counts | <https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications> |

### Evidence grade

`MEASURED` for the directive list, the linker behavior and expiry, the filter limits and timing, the referral cap, and the seven switches, from the pages above read on 2026-11-08. `LOCAL` for the recommendation to try the Testing state first and for the rule that a filter's direction must be checked before reporting a gap; those are this package's practice, not Google instructions.
