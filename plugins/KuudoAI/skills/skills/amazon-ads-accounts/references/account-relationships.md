# Account relationships

## Relationship model

A manager account (`managerAccountId`, beginning with `amzn1.ads1.ma1.`) groups and grants access to advertiser accounts. It may also participate in a parent-child hierarchy with another manager account. It is distinct from both an advertiser account and a marketplace profile.

This reference covers read-only relationship discovery. Association, disassociation, manager-account creation, and other mutations are outside this skill.

## Choose the query

| Question | Tool |
|---|---|
| “Which manager accounts can I access?” or “What do I manage?” | `ac_getManagerAccountsForUser` |
| “Which accounts are linked to this manager?” | `ac_getManagerAccountsForUser`, then `allv1_QueryAccountLink` with `CHILD` to confirm the list |
| “Which manager is above this advertiser account?” | `ac_getManagerAccountsForUser`, then `allv1_QueryAccountLink` with `PARENT` to confirm the list |

Check only the tool required for the question. If that tool is unavailable, explain which relationship cannot be resolved; unrelated missing account tools do not block the request.

## List manager accounts

`ac_getManagerAccountsForUser` takes no arguments. It returns `managerAccounts[]`, each with `managerAccountId`, `managerAccountName`, and `linkedAccounts[]`.

Each linked row has `accountId`, `accountName`, `accountType`, and `marketplaceId`. `DSP_ADVERTISING_ACCOUNT` rows add a `dspAdvertiserId`, and `VENDOR` rows add a `profileId`. A linked `accountId` can be an `ENTITY...` value, so do not present it as an `advertiserAccountId`. Report the types the rows state.

Treat this list as what the call returned, not proof that no other relationships exist. Report the count you see rather than quoting a limit; one manager returned 60 linked rows on 2026-10-30.

## Find the manager above an account

Get the account's `alternateIds` from `allv1_QueryAdvertiserAccount`, then look for those IDs in each manager's `linkedAccounts`:

- `DSP_ADVERTISING_ACCOUNT` rows match on `dspAdvertiserId`.
- `VENDOR` rows match on `profileId`, or on `accountId` as `entityId`.

Match on IDs rather than names. Every linked row matched an account this way on 2026-11-02. A matched row is a listed link, so state it as one. Then try the link query with `PARENT`, and if it fails, say that other parents and nesting are unconfirmed.

## Query account links

`allv1_QueryAccountLink` takes flat arguments:

- `relationshipTypeFilter.include` is required and holds one direction, `CHILD` or `PARENT`.
- `accountIdFilter`, `accountNameFilter`, and `accountTypeFilter` narrow the results. `accountTypeFilter.include` accepts `ADVERTISER_ACCOUNT` and `MANAGER_ACCOUNT`.
- Follow `nextToken` when it is returned.

```python
links = await call_tool("allv1_QueryAccountLink", {
    "relationshipTypeFilter": {"include": ["CHILD"]},
    "accountTypeFilter": {"include": ["MANAGER_ACCOUNT"]},
    "maxResults": 100,
})
```

This call returned 401 in every scope tried on 2026-10-30. If it fails, report the failure and say that nesting and completeness cannot be confirmed. Do not read either one from the linked-account list.

## Report the topology

Present each manager and advertiser account with its type and identifier. Preserve direction explicitly—“manager A is the parent of advertiser B”—rather than returning an unlabeled list of IDs. If the response contains nested manager accounts, identify them as manager nodes rather than advertiser accounts.

## Authoritative reference

- [Amazon Ads nested manager accounts](https://advertising.amazon.com/resources/whats-new/nested-manager-accounts)
