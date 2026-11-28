# Cutover evidence example

Illustrative, not a live redirect instruction. Record old origin, new origin,
request timestamp, method, observed chain, final canonical, and owner.

| Old path | Decision | Expected HTTP | Proof needed |
|---|---|---|---|
| /guides/retainer | Redirect to /services/retainer-guide | Single permanent redirect; final 200 | Destination retains guide, clean canonical, listed in new sitemap |
| /private/retainer | Keep the restricted behavior | Existing auth requirement | Authorized test still requires session; not in sitemap |
| /promotions/2021 | Retire; no useful replacement | 410 or equivalent intentional retirement | Not linked internally; record that this is intentional |

## Order at release

Confirm previous production configuration is recoverable. An authorized
operator deploys the new site and old-origin route changes in the planned
order; the reviewer then replays the priority inventory on both origins.
If an old key landing page cannot reach its equivalent, capture the request
and honor the agreed cutover thresholds. If a redirect cache prevents an
immediate rollback, verify actually served responses after the rollback
instead of assuming the provider setting took effect.

Separate internal hardening and sign-off from the eventual indexing outcome:
Search Console may not yet support a verdict on migration performance
even while direct redirect tests pass.
