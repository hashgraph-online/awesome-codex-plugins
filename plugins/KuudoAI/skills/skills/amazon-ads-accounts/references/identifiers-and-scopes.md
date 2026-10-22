# Identifiers and scopes

## Account model

An advertiser account is the unified advertiser identity across sponsored ads, Amazon DSP, and supported regions. Its `alternateIds` connect that global identity to marketplace profiles and other platform-specific identifiers. A profile is a marketplace-specific compatibility scope used by APIs that still request `profileId`.

| Identifier | Shape | Use |
|---|---|---|
| `advertiserAccountId` | `amzn1.ads-account.g.*` for global accounts; regional segment for legacy accounts | Advertiser-account APIs and account-level access |
| `profileId` | Numeric | Marketplace-specific alternate scope when explicitly requested by a campaign, eligibility, or reporting tool |
| `entityId` | Often `ENTITY...` | Alternate or legacy reference; never substitute it for an advertiser account ID |
| `dspAdvertiserId` | Returned in `alternateIds` when applicable | DSP operations that explicitly request this identifier |
| `countryCode` | Two-letter country code in `alternateIds` | Selects the marketplace-specific profile |

A `profileId` is globally unique, but it represents one advertiser in one marketplace. A multi-marketplace advertiser therefore has multiple profile IDs.

The advertiser account is the primary account concept. Start with it, then translate to a profile or alternate identifier only when the downstream tool's contract requires one.

## Discover advertiser accounts

Use `account_management-query_advertiser_account` for advertiser-account discovery.

- With no `isGlobalAccountFilter`, it returns global accounts by default.
- `isGlobalAccountFilter: { "include": [true] }` explicitly requests global accounts.
- `isGlobalAccountFilter: { "include": [false] }` requests non-global legacy or regional accounts.
- `advertiserAccountIdFilter.include` accepts global `amzn1.ads-account.g.*` IDs only.
- Use `nextToken` until the requested account is found or the result set is exhausted.
- There is no server-side account-name filter; match names client-side after listing.

To show all account types, make one global query and one non-global query, paginate both, then label the combined results.

```json
{
  "body": {
    "isGlobalAccountFilter": {
      "include": [false]
    },
    "maxResults": 100,
    "nextToken": "cursor-from-the-previous-page"
  },
  "skill": {
    "skillName": "amazon-ads-accounts",
    "version": "1.1.0"
  }
}
```

## Select the correct scope

### Starting from an account name

1. Query global advertiser accounts and paginate.
2. If the account is absent, query non-global accounts and paginate.
3. Present multiple plausible matches rather than choosing by fuzzy name similarity.
4. Retain the selected account for the current session.

### Starting from a global advertiser account ID

Query with `advertiserAccountIdFilter.include`, then use the returned account. This filter cannot resolve a non-global ID.

### Starting from a non-global advertiser account ID

Query non-global accounts without `advertiserAccountIdFilter`, paginate, and match the returned ID client-side.

### Resolving a profile ID

1. Resolve the advertiser account.
2. Inspect its `alternateIds` entries.
3. Select the entry matching the requested `countryCode`.
4. If the marketplace is not known and several entries exist, ask the user to choose.
5. Use the selected entry's numeric `profileId` only where the downstream tool requests profile scope.

The account query already returns `alternateIds`; a second lookup is unnecessary when the desired entry is present.

## Presenting choices

Show enough information to distinguish accounts without exposing unrelated details:

- Display name
- Advertiser account ID
- Global or non-global status
- Available marketplace country codes
- Profile ID only when it helps make the requested selection

If exactly one account or marketplace profile is valid, select it and tell the user what will be used. If multiple remain valid, ask the user to choose.

## Authoritative reference

- [Amazon Ads advertiser account guide](https://advertising.amazon.com/en-gb/library/guides/advertiser-account)
