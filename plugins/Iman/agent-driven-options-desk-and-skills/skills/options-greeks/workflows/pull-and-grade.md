# Workflow: pull a chain and grade it

Run in order. Each step writes one artifact the next step reads.

1. `optiondesk expiries SYM` to see what the provider lists and what is
   already on disk. Choose an expiry with the days to expiry in view; a
   one day chain and a ninety day chain answer different questions.
2. `optiondesk chain SYM --expiry YYYY-MM-DD`. Read `with_iv` against
   `contracts` in the summary. A large gap means many contracts had no
   two sided quote, which is normal in the wings and abnormal at the money.
3. `optiondesk greeks --band 0.06`. The band is a fraction of spot. Widen
   it to see the wings, set it to 0 to grade every strike.
4. Report from the summary, not from your own arithmetic. Quote
   `atm_sample` for a single representative contract.

## Before reporting

Check `degraded` in the artifact meta and say so first if it is true.

State the expiry and `spot_asof`. The spot is the last settled close,
which on a weekend or before the open is not today.

If the user asks for a number the ladder skipped, say it was skipped and
why, rather than computing something else and presenting it as the answer.
