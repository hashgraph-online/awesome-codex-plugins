# Integration Guidance

The portable skill can propose from a complete local run bundle. Live operation
requires an Amazon Ads integration; warehouse and sandbox runners are optional.
Tool names vary by deployment, so discover current schemas rather than copying
names or payloads from examples.

## Capability ownership

| Need | Required capability | Mutation? |
|---|---|---|
| Resolve advertiser, profile, marketplace, currency, timezone | Amazon Ads account agreeddiscovery | no |
| Read campaigns, state, budget type, and current daily budget | Sponsored Ads campaign read | no |
| Read overdelivery setting and active budget rules | Sponsored Ads settings/rules read | no |
| Read spend, attributed sales, and time-in-budget | Amazon reports or governed warehouse | no |
| Update a campaign daily budget | Sponsored Ads campaign budget update | yes |
| Pause a campaign | Sponsored Ads campaign state update | yes |
| Run allocator and renderer headlessly | Python 3.10+ or sandbox runner | local artifacts only |

## Account resolution

Use `amazon-ads-accounts` when available. Resolve the identifier type requested
by the downstream tool; advertiser account IDs, profile IDs, entity IDs, DSP
advertiser IDs, and manager-account IDs are not interchangeable.

For more than one plausible advertiser or marketplace profile, present the
choices and ask the user to select. Capture the selected account, profile,
marketplace, currency, and IANA timezone in `account_context`. Repeat them in the
proposal and verify them again before mutation.

## Read path

Discover the live tool schemas for:

1. campaign listing, including state and budget type;
2. average-daily-budget overdelivery settings;
3. active schedule- and performance-based budget rules;
4. reporting creation, retrieval, and download;
5. budget and campaign-state updates.

Reject lifetime, portfolio, DSP, or unrecognized budget types. The allocator
supports only confirmed campaign-level daily monetary budgets.

Active Amazon budget rules can cumulatively increase budgets. This revision does
not model their effect, so a non-empty `active_budget_rules` array blocks the
run. Disabling rules is a separate mutation requiring its own proposal and
authorization.

## Performance data

Spend can be read through the most recently completed account-local day and may
still be preliminary. Attributed sales mature later, so compute campaign ROAS
with a window ending at least two completed days before `as_of`. Record both
`data_through` and `roas_data_through` in the run bundle.

Record concrete sources and retrieval timestamps. A warehouse table, exported
report, upload, manual value, and synthetic fixture must remain distinguishable
in the final provenance footer.

If recurring collection is managed by a separate operator, hand it the selected
account context, required report windows, cadence, and destination. Do not claim
that a schedule exists until the owning system confirms it.

## Commit path

Approval applies only to the displayed `proposal_id` and account context. Before
writing:

1. re-resolve the selected account/profile;
2. re-read campaign states, budgets, overdelivery setting, and budget rules;
3. compare them with the approved proposal;
4. abort and regenerate on any drift or after the account-local `as_of` date.

Send `proposed_changes[]` through the tool's documented budget-update operation
using `account_context.currency_code`. Send `pause_campaign` entries through a
campaign-state update. Do not substitute a budget value of zero.

Prefer a documented atomic batch. Otherwise retain item-level results and stop
after a failure unless the user approved independent best-effort updates. Report
succeeded, failed, and unattempted items, then read back live state. Any retry
requires renewed authorization against that state.

## Scheduling

Scheduled execution may collect data, assemble a bundle, run `allocate.py`, run
`report.py`, and deliver the proposal. It does not imply permission to write.
Unattended live mutation requires a separately defined policy covering account
scope, campaigns in scope, allowed operations, change bounds, expiration,
failure behavior, notification, and revocation. The user approves that policy
with an explicit yes after seeing it in full; the SKILL.md Scheduling section
sets what an unattended run may and may not do. Disabling budget rules and
retrying failed writes are never unattended.

## Authoritative Amazon references

- [Sponsored Products budget guidance](https://advertising.amazon.com/library/guides/sponsored-products-budget-best-practices)
- [Sponsored Ads daily-budget overdelivery settings](https://advertising.amazon.com/resources/whats-new/sponsored-ads-daily-budgeting-policy-and-options)
- [Sponsored Ads budget rules](https://advertising.amazon.com/help/GNSMLANWNF344YBE)
- [Performance-metric freshness](https://advertising.amazon.com/help/GG44RFW942U9F6F5)
- [ROAS reporting delays](https://advertising.amazon.com/help/G78DVL9PAZZ83KQX)
