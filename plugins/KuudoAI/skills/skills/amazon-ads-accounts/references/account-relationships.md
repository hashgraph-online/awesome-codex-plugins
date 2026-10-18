# Account relationships

## Relationship model

A manager account (`managerAccountId`, beginning with `amzn1.ads1.ma1.`) groups and grants access to advertiser accounts. It may also participate in a parent-child hierarchy with another manager account. It is distinct from both an advertiser account and a marketplace profile.

This reference covers read-only relationship discovery. Association, disassociation, manager-account creation, and other mutations belong to an account-administration workflow and require their own confirmation rules.

## Choose the query

| Question | Tool |
|---|---|
| “Which manager accounts can I access?” or “What do I manage?” | `manager_accounts-get_manager_accounts` |
| “Which accounts are linked to this manager?” | `account_management-query_account_link` with the manager ID and `CHILD` |
| “Which manager is above this advertiser account?” | `account_management-query_account_link` with the advertiser account ID and `PARENT` |

Check only the tool required for the question. If that tool is unavailable, explain which relationship cannot be resolved; unrelated missing account tools do not block the request.

## List manager accounts

`manager_accounts-get_manager_accounts` takes no account identifier. It returns the authenticated user's manager accounts and up to 50 linked accounts per manager. Treat that embedded list as a bounded summary, not proof that no additional relationships exist.

```json
{
  "skill": {
    "skillName": "amazon-ads-accounts",
    "version": "1.1.0"
  }
}
```

## Query account links

`account_management-query_account_link` requires:

- `accessRequestedAccount` containing exactly one `advertiserAccountId` or `managerAccountId`.
- `relationshipTypeFilter.include` containing one relationship direction.
- Pagination with `nextToken` when returned.

Query the children of a manager account:

```json
{
  "body": {
    "accessRequestedAccount": {
      "managerAccountId": "amzn1.ads1.ma1.xxxxx"
    },
    "relationshipTypeFilter": {
      "include": ["CHILD"]
    },
    "maxResults": 100
  },
  "skill": {
    "skillName": "amazon-ads-accounts",
    "version": "1.1.0"
  }
}
```

Query the parent of an advertiser account by replacing `accessRequestedAccount` with its `advertiserAccountId` and using `PARENT`.

## Report the topology

Present each manager and advertiser account with its type and identifier. Preserve direction explicitly—“manager A is the parent of advertiser B”—rather than returning an unlabeled list of IDs. If the response contains nested manager accounts, identify them as manager nodes rather than advertiser accounts.

## Authoritative reference

- [Amazon Ads nested manager accounts](https://advertising.amazon.com/resources/whats-new/nested-manager-accounts)
