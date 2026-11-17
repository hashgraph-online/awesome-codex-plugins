# Promo, trial and referral abuse

**Class id:** `promo-and-referral-abuse`

Anything given away to attract users will be collected by people who are not the users you wanted, and by their scripts. The question is not whether a bonus can be claimed, but how many times and at what cost to the claimer.

## Where to look

Coupon and promo code redemption, sign-up bonuses, free trials, referral programs, daily rewards, first-purchase discounts, gifting and transfer features that can move bonus value between accounts.

## Shapes that are bugs

**A code with no memory.**

```js
const promo = PROMOS[code.toUpperCase()];
if (!promo) return res.status(404).end();
await addBalance(user.id, promo.coins);       // the same account can call this all day
```

Look for a redemption record with a unique constraint on (code, account), and for a cap on total redemptions that is enforced atomically.

**Guessable codes.** Short or sequential codes on an endpoint without attempt limits. A script can find valid ones.

**Stacking.** Several codes applied to one order, or one code applied to every item, where the intent was one discount.

**Referral bonus on sign-up.** The referrer is paid the moment an account is created with their code. Creating accounts costs nothing, so the bonus is unlimited:

```python
if referrer:
    referrer.balance += REFERRAL_BONUS     # paid for an email address
```

Related: self-referral through a second account, both-sided bonuses that pay the farmer twice, and bonuses that stay when the invited account is deleted or banned.

**Trials that restart.** A new trial for every new account, with accounts distinguished only by an email string. `name+1@gmail.com`, `n.a.m.e@gmail.com` and a disposable address are all new strings. Also: a trial that restarts after cancel and resubscribe, or after deleting and recreating the account.

**Bonus value that can leave.** Sign-up, promo or referral credits that can be withdrawn as cash, or transferred to another account and withdrawn there. Many accounts, one cash-out.

**Daily claims on the client's clock.** A daily reward keyed to a date the client sends, or to a time zone the user can change at will.

**No velocity limits.** Unlimited sign-ups, redemptions or claims per IP address, device or payment instrument.

## What correct looks like

- One redemption per account, enforced by a unique key. Global caps enforced in the same transaction.
- Codes long and random enough that guessing is pointless, with attempt limits anyway.
- Referral rewards paid only after the invited user does something that costs real effort or money and that the server verified: a completed payment, a verified offer, a period of genuine activity. Paid once per invited user, and taken back if that activity is reversed.
- Trials tied to something harder to mint than an email string: a normalized email, a payment method fingerprint, a verified phone number.
- Bonus value is spendable but not withdrawable, or is withdrawable only after matching earned activity.
- Sign-up risk checks: disposable email domains, datacenter addresses, velocity. These reduce volume; the rules above remove the incentive.

## How to prove it

```bash
node scripts/probe.mjs replay promo.json --times 3 --observe me.json     # same code, same account
node scripts/probe.mjs race promo.json --parallel 10 --observe me.json   # past a per-code cap
```

For referral and trial abuse, create two or three accounts through the normal sign-up endpoint and show the bonus arriving with no further activity. Three sign-ups are a proof; do not script hundreds.

## Not a bug

- A code that is meant to be reusable (a public 10 percent discount on paid orders) and only reduces a price that is still paid.
- A referral bonus that is small, not withdrawable, and capped per referrer, where the business has chosen growth over strictness. Record the choice as the note.
- Multi-account abuse that would need many verified payment methods or phone numbers. The cost to the abuser is the control.

## Severity

Unlimited free value that can be withdrawn: critical. Unlimited free value that can only be spent in the app: high. A weak trial restart control on a product with real per-user cost: medium to high, depending on that cost.
