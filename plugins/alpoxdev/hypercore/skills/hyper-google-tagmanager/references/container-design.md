# Container Design

Read this file in `configure`, and whenever a finding is about the dataLayer, tags, triggers, variables, templates, ecommerce, workspaces, or server-side tagging. Facts marked `volatile` change with the product.

## Contents

- 1. Event plan
- 2. dataLayer contract
- 3. Google tag and GA4 event tags
- 4. Ecommerce
- 5. Triggers and firing control
- 6. Variables, templates, and Custom HTML
- 7. Workspaces, versions, permissions, import, naming
- 8. Server-side tagging
- Sources

## 1. Event Plan

Write one row per tag before touching code or the container:

| Event | Trigger | Parameters | Destination | Consent type |
|---|---|---|---|---|
| `purchase` | Custom Event `purchase` | `transaction_id`, `value`, `currency`, `items` | GA4 `G-...` | `analytics_storage` |
| `generate_lead` | Form submission, `Form ID` equals `contact` | `form_id` | GA4, Google Ads conversion | `analytics_storage`, `ad_storage`, `ad_user_data` |

- Use Google's recommended event names (`purchase`, `add_to_cart`, `generate_lead`, `sign_up`, `login`, `search`, ...) before inventing one. Event names are case-sensitive.
- No personal data in names or parameters (`rules/safety-gates.md` §4).

## 2. dataLayer Contract

- Create the dataLayer before the container loads: `window.dataLayer = window.dataLayer || [];`. "Only one `dataLayer` object is supported per page." Never assign `window.dataLayer = []` after GTM loads; tags stop firing and data is lost.
- Push events with `dataLayer.push({ event: 'event_name', key: 'value' })`. A later push of the same key overwrites the value.
- Values do not persist across page loads. A value needed at container load must be pushed on every page, above the container snippet.
- `dataLayer` is case-sensitive (`datalayer.push` fails); keys must be valid quoted object keys; use one name per concept across pages.
- GTM processes messages first in, first out, one at a time. Pushes made from inside a tag or template are queued behind pending messages, so "any updated data layer values are not guaranteed to be available for the next event": give them their own `event` and a Custom Event trigger.
- In a tag-sequencing setup tag, change values with `google_tag_manager[{{Container ID}}].dataLayer.set()`, not `push`.
- Long-lived single-page apps can clear state with a pushed function that calls `this.reset()`.
- Do not use Custom HTML tags to deploy gtag.js code or to set consent; use native templates and the consent APIs.

## 3. Google Tag and GA4 Event Tags

- The **Google tag** (tag type Google Analytics > Google tag, Tag ID `G-...`) fires on **Initialization - All Pages**. It loads the property, declares common settings, sets cookies, and sends automatically collected and enhanced measurement events.
- **Google Analytics: GA4 Event** tags send one event each: Measurement ID plus Event Name plus parameters. Prefer the Google tag's ID through a constant variable.
- Reuse settings with two variable types:
  - **Google tag: Configuration settings**: config-level keys such as `send_page_view` (default `true`), `cookie_domain` (default `auto`), `cookie_expires` (default `63072000` seconds), `user_id` (up to 256 characters), `server_container_url`.
  - **Google Tag: Event Settings**: parameters shared by many event tags, and GA4 user properties (up to 25 per property).
- Destinations (`volatile`, 2026-10-12): containers can send to Google destinations directly without loading gtag.js; Settings > Google Destinations lists them. Central settings apply to destination tags, not to a separately loaded Google tag.
- Since 2025-04-10 containers with Google Ads or Floodlight tags load a Google tag first (`volatile`).

## 4. Ecommerce

Clear, then push, for every ecommerce event:

```js
dataLayer.push({ ecommerce: null });  // Clear the previous ecommerce object.
dataLayer.push({
  event: "purchase",
  ecommerce: {
    transaction_id: "T_12345",
    value: 72.05,
    tax: 3.60,
    shipping: 5.99,
    currency: "USD",
    coupon: "SUMMER_SALE",
    items: [{
      item_id: "SKU_12345",
      item_name: "Stan and Friends Tee",
      price: 10.01,
      quantity: 3,
      item_brand: "Google",
      item_category: "Apparel",
      item_variant: "green",
      index: 0
    }]
  }
});
```

- Event names: `view_item_list`, `select_item`, `view_item`, `add_to_cart`, `add_to_wishlist`, `view_cart`, `remove_from_cart`, `begin_checkout`, `add_shipping_info` (`shipping_tier`), `add_payment_info` (`payment_type`), `purchase`, `refund`, `view_promotion`, `select_promotion`.
- `purchase` and `refund` need `transaction_id` (deduplication). `value` needs `currency` as a three-letter ISO 4217 code at the event level.
- `items`: up to 200 entries; each needs `item_id` or `item_name`; `quantity` defaults to 1; up to 27 custom item parameters (the documentation does not say whether per item or per array; plan per item).
- In GTM: one GA4 Event tag per event with **Send Ecommerce data** turned on (data source Data Layer), on a Custom Event trigger with that event name. The alternative is Data Layer Variables (`ecommerce.items`, `ecommerce.transaction_id`, ...) mapped to parameters.
- Push `purchase` only once per order (server-confirmed thank-you page or after payment success), and keep `transaction_id` stable across reloads.

## 5. Triggers and Firing Control

- Page-load order: **Consent Initialization** (CMP and consent defaults) -> **Initialization** (Google tag) -> **Page View** -> **DOM Ready** (`gtm.dom`) -> **Window Loaded** (`gtm.load`). Fire non-essential tags on Window Loaded.
- Other trigger types: Click (All Elements, Just Links with Wait for Tags and Check Validation), Form submission (Wait for Tags, Check Validation), Scroll Depth (once per threshold per page), Element visibility (default 50% visible; once per page, once per element, or every time), YouTube video, Custom event (optional regex), History change (fragment or `pushState`), JavaScript error (uncaught only, after GTM loads), Timer (`gtm.timer`), Trigger group (fires after every member fired at least once).
- Never use a Custom Event trigger with regex `.*`: it matches every GTM and Google tag event, including `gtag.config` since 2026-10-08.
- A tag fires when any of its firing triggers match; exceptions (blocking triggers) stop it. Every tag needs at least one firing trigger.
- Firing options: Once per event, Once per page, Unlimited (sequencing only). Priority numbers do not guarantee order ("Tags will still fire asynchronously"); use tag sequencing (setup and cleanup tags) when order matters.
- Pause or remove unused tags instead of blocking them with an exception; pausing removes the code from the container.

## 6. Variables, Templates, and Custom HTML

- Built-in variables to enable as needed: Clicks, Forms, History, Pages, Scroll, Utilities (Container ID, Container Version, Environment Name, Event, and since 2025-12 Analytics Client ID, Session ID, Session Number), Videos, Visibility.
- Data Layer Variable (version 2) reads nested keys such as `ecommerce.value`. Lookup and RegEx tables replace near-duplicate tags.
- Custom templates run sandboxed JavaScript (ECMAScript 5.1 with some ES6) with declared permissions (`inject_script`, `send_pixel`, `access_globals`, `read_data_layer`, `get_cookies`, ...). URL match patterns must use HTTPS and name host and path. Prefer a Community Template Gallery template over Custom HTML.
- Custom HTML runs unsandboxed page script: review the vendor code, load large libraries from a `<script src>`, and enable **Support document.write** only when the vendor code needs it. GTM minifies Custom HTML, which can turn single quotes into double quotes in version diffs.
- Custom JavaScript variables evaluate to `undefined` under a CSP without `'unsafe-eval'` (`references/install-recipes.md` §5).
- Restricting tag types: `gtm.allowlist` and `gtm.blocklist` pushed before any tag fires; blocklists win; blocking any class also blocks sandboxed templates unless `sandboxedScripts` is allowlisted. Google now steers to custom templates plus template policies (`gtag('policy', ...)`); a deny-all policy stops measurement unless `read_event_data`, `read_container_data`, and `configure_google_tags` are allowed.

## 7. Workspaces, Versions, Permissions, Import, Naming

- Workspaces: a standard account allows 3 concurrent workspaces (the default plus 2); Tag Manager 360 allows unlimited. A version or publish removes the workspace; other workspaces then show "out of date" and must be updated.
- Versions: a version is a snapshot; Submit > Publish and Create Version, or Create Version only. Approvals (Request Approval) exist in Tag Manager 360 only.
- Container permissions: No access, Read, Edit (workspaces and edits, no versions), Approve (versions, no publish), Publish. Account roles: Administrator, User. Turn on 2-step verification for Custom HTML, Custom JavaScript, and user settings.
- Import (Admin > Import Container): **Overwrite** removes all existing tags, triggers, and variables and creates a version first; **Merge** with **Overwrite conflicting** or **Rename conflicting**. Always import into a new workspace, read View Detailed Changes, and treat Overwrite as approval-tier.
- Size: GTM limits a container to 300 KB and shows a Size indicator; act above 70%.
- Naming: `<type> - <destination> - <detail>`, for example `GA4 - Event - purchase`, `CE - purchase` for the trigger, `DLV - ecommerce.value` for the variable, with folders per destination or team. One container per web domain; one container for several domains that form one experience.

## 8. Server-Side Tagging

- A server container runs on a tagging server (Cloud Run by automatic provisioning, or manual on GCP or other hosts). Clients claim incoming requests; tags send outgoing ones.
- Cost and size (`volatile`): a 1 vCPU, 0.5 GB Cloud Run instance is about USD 45 per month; Google recommends at least 2 instances in the setup guide and 3 in the overview; 2 to 10 instances handle about 35 to 350 requests per second. The default deployment is for testing only. Creating or scaling it costs money: approval tier.
- Domain: same origin (`https://www.example.com/metrics`) is best, a subdomain (`https://metrics.example.com`) next; the default `run.app` domain cannot set server cookies.
- Web connection: add `server_container_url` to the Google tag's configuration settings. Since 2025-06-30 serve gtag.js and gtm.js through the web container client (`volatile`).
- Verify with the server container's own Preview (Request, Tags, Variables, Event Data, Console tabs) and `<server URL>/healthy` returning `ok`. Web Preview alone does not show server tag errors.
- CSP: `img-src` and `connect-src` need the server container URL, `frame-src` too for the service worker, and `X-Frame-Options` must not block it.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| dataLayer creation, one object, FIFO processing, persistence, Custom HTML prohibitions | <https://developers.google.com/tag-platform/tag-manager/datalayer> |
| Google tag and GA4 Event tags in GTM | <https://support.google.com/tagmanager/answer/9442095> |
| Ecommerce push shape, `ecommerce: null`, item limits, Send Ecommerce data | <https://developers.google.com/analytics/devguides/collection/ga4/ecommerce?client_type=gtm> |
| Page-load trigger order | <https://support.google.com/tagmanager/answer/7679319> |
| Trigger types and options | <https://support.google.com/tagmanager/topic/7679108> |
| Tag sequencing and `dataLayer.set()` | <https://support.google.com/tagmanager/answer/6238868> |
| Firing options and priority | <https://support.google.com/tagmanager/answer/6279951> |
| Built-in variables | <https://support.google.com/tagmanager/answer/7182738> |
| Custom templates and permissions | <https://developers.google.com/tag-platform/tag-manager/templates> |
| Custom HTML and document.write | <https://support.google.com/tagmanager/answer/6107167> |
| Allowlist, blocklist, template policies | <https://developers.google.com/tag-platform/tag-manager/restrict>, <https://developers.google.com/tag-platform/tag-manager/templates/policies> |
| Workspaces | <https://support.google.com/tagmanager/answer/7059647> |
| Versions, publishing, approvals | <https://support.google.com/tagmanager/answer/6107163> |
| Permissions | <https://support.google.com/tagmanager/answer/6107011> |
| Import and export | <https://support.google.com/tagmanager/answer/6106997> |
| Container size | <https://web.dev/articles/tag-best-practices>, <https://support.google.com/tagmanager/answer/2772488> |
| Release-note dates (2025-04-10, 2025-06-30, 2025-12-11, 2026-10-08, 2026-10-12) | <https://support.google.com/tagmanager/answer/4620708> |
| Server-side tagging | <https://developers.google.com/tag-platform/tag-manager/server-side>, <https://developers.google.com/tag-platform/tag-manager/server-side/cloud-run-setup-guide>, <https://developers.google.com/tag-platform/tag-manager/server-side/custom-domain> |

### Evidence grade

Official Google documentation read 2026-11-08. The naming pattern adapts Google's `<item type> - <app> - <detail>` example; the event-plan table is this package's design.
