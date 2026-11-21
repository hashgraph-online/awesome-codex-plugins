# Amounts trusted from the client

**Class id:** `client-trust`

The browser and the mobile app belong to the user. Anything they send can be changed: a price, a quantity, a number of credits, a plan name, a score, the id of the account to charge. The server must take such values from its own records.

## Where to look

Checkout and order creation, spending and transfers, reward claims ("level complete", "ad watched", "daily bonus"), subscription changes, profile update endpoints, and the client code that calls them. Read the client: every field it sends is a candidate.

## Shapes that are bugs

**The price or the grant comes from the request.**

```js
const order = await Orders.create({
  userId: req.user.id,
  pack: req.body.pack,
  credits: req.body.credits ?? PACKS[req.body.pack].credits,   // the client may send any number
  amount: req.body.amount,                                      // and any price
});
```

The payment may be genuine and correctly verified. The order it pays for was written by the user.

**The total is computed in the browser.** The server receives `total` or `discountedPrice` and charges it, instead of recomputing from item ids, quantities and the coupon.

**Quantity and sign.** `quantity: -3` turns a charge into a credit. `quantity: 0.001` buys a fraction. Covered in detail under money arithmetic; report the missing server-side check here when the client value reaches a price.

**The reward is claimed, not earned.** `POST /api/reward { "coins": 50 }` or `POST /api/level-complete { "score": 999999 }` with no server-side evidence that anything happened. Game scores, watched-ad claims and step counters posted by the client are all of this kind.

**The entitlement is decided client-side.** A premium flag in local storage, in a cookie the client can write, or in a token whose claims the server does not re-check. A mobile purchase unlocked on the device without validating the receipt on the server.

**Mass assignment.**

```php
$user->update($request->all());        // {"balance": 999999, "plan": "pro", "is_admin": true}
```

Any endpoint that copies the request body into a database row can set money fields unless they are excluded. Check the allow list, not the form.

**The account is named by the request.** `from`, `user_id` or `wallet_id` taken from the body or the URL where the session should decide. Report it under `secrets-and-access` when it lets one user act on another's money.

**Currency and plan switching.** A `currency` field that reprices an order with the same number, or a `plan` field accepted on an endpoint meant for something else.

## What correct looks like

- The client sends identifiers and intent: which pack, which item, how many. The server looks up prices, computes totals, applies discounts and decides entitlements.
- When a provider's event confirms payment, the handler compares the paid amount and currency with the server's own order before granting anything.
- Rewards are granted on evidence the server can check: a verified server-to-server callback, a validated receipt, server-side game state.
- Update endpoints copy an explicit list of fields.

## How to prove it

```bash
node scripts/probe.mjs send checkout.json --set-body credits=1000000
node scripts/probe.mjs send checkout.json --set-body amount=1
node scripts/probe.mjs send profile.json --set-body balance=999999 --observe me.json
node scripts/probe.mjs send claim.json --set-body coins=50000 --observe me.json
```

For an order, follow it to the end: create it with the changed value, complete the payment step with a correctly signed test event, and observe the balance.

## Not a bug

- The client sends a price for display or logging and the server ignores it when charging. Confirm by reading where the charged amount comes from.
- The server recomputes or validates the value before use (a price lookup, a schema that rejects unknown fields).
- A value is client-supplied by design and bounded server-side, such as a tip or a pay-what-you-want amount with a minimum.

## Severity

Free or arbitrary credits for any signed-in user: critical, and that includes an unbounded grant attached to a small genuine payment. A lower price that still has to be paid, for the normal grant: high. A client-side entitlement check with a correct server check behind it: not a finding.
