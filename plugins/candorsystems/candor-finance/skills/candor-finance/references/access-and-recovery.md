> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Access and recovery

## Candor tools are missing

If no Candor tools are available in this session, send the person (or
yourself, if you can install things) to `https://candor.money/START.md`. It
has the connection details and package for every supported agent.

## The opening asks for an account step

Some openings return an action instead of records: the account is not set
up, or a business workspace's access lapsed. Pass through the exact
`safe_url` or `recovery_url` Candor returned, say in one sentence what the
person needs to do there, and try again once they are back. Account setup,
subscriptions, payment, and connecting banks happen only on secure
`https://app.candor.money` pages. With no specific link, banks are connected
and reconnected on `https://app.candor.money/accounts`, and the rest is on
`https://app.candor.money/settings`. Never ask for passwords, codes, or
account numbers in chat.

## No history to read yet

- **A sync is still running:** say the first sync is filling in, and open
  again once it finishes. Do not report empty months as no spending.
- **No accounts yet:** a free workspace starts here. Add the person's
  accounts and history from what they share (see `candor-add-records`);
  Candor works from those records the same way. Connecting banks is optional, US
  institutions only, on the Personal plan the person starts on the web.
- **A bank that stopped:** list connections before suggesting a new one. A
  connection that errored needs repair on the web, not a second connection.
- **Every account is excluded:** an account needs including. Check its
  inclusion with `candor_get({"operation":"accounts.policy.get","reason":"Check whether the account is included","args":{"account_identity_id":"ACCOUNT_ID"}})`; set it with
  `candor_write({"operation":"accounts.policy.set","reason":"Set the account role the person described","input":"<accounts.policy.set input object; candor_schema lists its fields>"})` when the person says to.
- **Balances only:** say which question transaction history would answer.
- **Accounts kept by hand:** each is current only through its
  `records_through` date in the opening's coverage. When one runs behind, ask
  for its newer statement or export; there is nothing to refresh.

## An outdated package

A package behind the latest release needs no update. Only when the opening
returns `agent_package_unsupported`, finish what still works, then run its
`agent_package.update` next actions in order once the person agrees, and
reload or start a new session when told to.
