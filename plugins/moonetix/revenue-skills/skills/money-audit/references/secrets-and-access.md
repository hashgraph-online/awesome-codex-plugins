# Secrets and access on the money path

**Class id:** `secrets-and-access`

This class covers who may call the code that moves money and which keys they need. It is limited to the money path: a leaked analytics key is someone else's audit, a leaked payment secret is this one.

## Where to look

Configuration loading, environment examples, client bundles and mobile app code, admin and support endpoints, any endpoint that takes an account, order or wallet id as a parameter, database security rules, and routes named `test`, `debug`, `dev` or `internal`.

## Shapes that are bugs

**A secret the client can read.** A payment provider's secret key, a webhook signing secret, a postback key, an admin token or a database service-role key that appears in JavaScript served to browsers, in a mobile app, or in a public repository.

```js
// assets/support-panel.js, served to every visitor
const SUPPORT_TOKEN = 'sk_support_8f2c...';
fetch('/internal/adjust-balance', { method: 'POST', headers: { 'x-support-token': SUPPORT_TOKEN }, body });
```

Search built assets as well as sources. Variables that a framework exposes to the client by prefix (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_`) are public by design; a secret in one is a finding.

**A default that works.** `process.env.ADMIN_KEY || 'admin'`. If the variable is ever unset in production, the default is the key. Secrets on the money path must have no fallback, and the app should refuse to start without them.

**One user acting on another's money.**

```python
@app.post("/api/transfer")
def transfer(body: TransferIn, user=Depends(current_user)):
    sender_id = body.from_user or user.id          # the caller chooses whose wallet pays
```

The same flaw as a read: `GET /api/wallets/{id}`, `/orders/{id}`, `/payouts/{id}` returning any account's data, or accepting changes to it, with no check that the id belongs to the session.

**An admin endpoint with user-level protection.** A balance adjustment or refund route that checks only that someone is signed in, or checks a role stored in something the user can edit. Also look for the absence of limits. A route that staff alone can reach but that records no actor is a `ledger-and-audit-trail` finding, rated by the rule in that class.

**Routes left over from development.** `/api/test/add-credits`, `/debug/set-balance`, a seed endpoint, a GraphQL mutation used by a test harness. If the route exists in production code and is reachable, it is a finding regardless of intent.

**The database is the API.** With client-side database access, the security rules decide. A rule that lets an authenticated user update their own row lets them update the `balance`, `credits` or `plan` column in it:

```sql
create policy "users update own row" on profiles
  for update using (auth.uid() = id);      -- every column, including credits
```

Money columns belong in a table clients cannot write, changed only by server-side code.

**Server-side calls with the user's choice of target.** An endpoint that fetches a URL, calls a provider or sends a payout to a destination taken from the request without checking it against the account.

**Secrets in logs and errors.** Webhook bodies with signatures, provider keys in error messages, full card or bank details in application logs.

## What correct looks like

- Secrets live in the server environment or a secret manager, have no defaults, and are required at start-up.
- The account acted on is always the session's account. Ids in requests are checked for ownership.
- Admin actions need an admin identity verified server-side, are limited in size, require a reason, and are written to an audit trail.
- Test and debug routes are not registered in production builds.
- Clients cannot write money columns. Balance changes happen in server code that the rules call, not in the rules themselves.

## How to prove it

```bash
node scripts/probe.mjs send transfer.json --set-body from=2 --observe me.json      # another account as the source
node scripts/probe.mjs send grant.json --set-header x-admin-key=VALUE_FROM_PUBLIC_FILE --observe me.json
node scripts/probe.mjs send wallet.json --set-query id=2                           # read another account
```

For an exposed secret, cite the file and line where it is served or committed, and show one request that uses it. Do not write the secret's value into the finding: quote the variable name and enough of the line for the validator.

## Not a bug

- Publishable keys that providers intend for client use.
- An id in the URL that the handler checks against the session before use.
- A debug route registered only when a server-side flag is set that production configuration does not set. Note it as a risk if nothing enforces that.

## Severity

A reachable secret or endpoint that lets any user grant or move value: critical. Reading other accounts' financial data: high. A working default secret that production currently overrides: medium.
