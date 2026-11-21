---
name: risk-portfolio
description: Aggregate gross and net exposure, gross and net leverage against a supplied NAV, and each asset's share of gross for signed linear positions in one base currency (risk_exposure). Use when the user asks for gross or net exposure, leverage, or which asset is the biggest share of the book. Not for options (use risk-derivatives), counterparty exposure at default (use risk-counterparty), or grading limits (use risk-limits).
---

# Risk Portfolio

One tool, `risk_exposure`, with the PortfolioRequest contract in
[input contracts](../../references/contracts.md). CLI:
`riskdesk exposure --input PATH`. Examples: `examples/portfolio.json`,
`examples/energy_book.json`.

Require signed market values already translated into the stated currency
and an explicit NAV. Confirm that each position is a linear asset. Options
require sensitivities or full revaluation; premium market value is not
delta exposure. For a book with European options use
`risk_derivatives_greeks`, `risk_derivatives_grid` and
`risk_derivatives_historical` (the risk-derivatives skill), whose book
contract is separate from this one.

## Report first

1. `degraded` and `degraded_reason`, before any number.
2. Gross before net, with currency and `as_of`.
3. `gross_leverage` and `net_leverage` as multiples of the supplied NAV.
4. The largest entry in `gross_shares`, as a percentage of gross.
5. A negative `net_by_asset` entry is a net short in that asset; say so in words.

## Sign conventions

Market values are signed: positive is long, negative is short. Gross adds
the absolute value of every position before any offsetting, so a long and
a short in the same asset both add to gross and cancel in net. Gross is
never below the absolute value of net, a share of gross is never negative,
and net leverage is negative for a net short book.

## What not to claim

- Do not describe these amounts as counterparty EAD, margin or regulated capital.
- NAV is the caller's figure; nothing here verifies it.
- No FX translation is done. A book in two currencies that was not converted first gives a confident and meaningless total.
- Research output, not investment advice.

## Going deeper

- `reference.md`: every formula with its source line, the envelope, and what is refused.
- `workflows/exposure-report.md`: run, check and report one book.
- `scripts/check_artifact.py RESULT.json`: re-derives leverage, net, the shares and the gross bounds from a saved result and prints a one line verdict. Standard library only.
