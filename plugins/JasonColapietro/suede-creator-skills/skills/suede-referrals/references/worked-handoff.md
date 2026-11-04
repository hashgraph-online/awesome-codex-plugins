# Suede AI Referral Skills: Worked Handoff

## Inputs

Request: “Design a referral pilot for a subscription service.” Synthetic business
inputs: $40 monthly revenue, $16 monthly variable delivery cost, a $10 reward to
each side, paid only after the referred customer's second paid month. No observed
referral conversion or retention data is supplied. Returns and fraud can reverse
eligibility; the business owner has not yet approved final terms.

## Expected output

Write the program spec with qualifying event, attribution window, deduplication,
self-referral rule, reward type, review owner, dispute path, disclosure language,
and rollout checklist. Show the illustrative contribution calculation:
`2 × ($40 − $16) − $20 = $28` before acquisition, fixed, tax, refund, or fraud
costs. Label those exclusions. Do not turn that example into LTV or expected
profit. Propose a capped pilot, with its cap left for the owner's real budget,
and report referral activation, paid conversion, net contribution, reversals,
and retention by cohort.

## Failure case

If variable costs, reward funding, or refund terms are unknown, return an
economics worksheet and unresolved decision rather than calling the incentive
sustainable. If referral evidence is incomplete, queue the reward for review;
do not issue a payout or create accounts while drafting a program.

## Validation

Recalculate the example from the supplied values. Trace every payout condition
to a named event and owner. Verify negative cases: self-referral, duplicate
customer, cancellation before month two, refund after eligibility, and disputed
attribution. The spec should state what each does to eligibility and appeal.
