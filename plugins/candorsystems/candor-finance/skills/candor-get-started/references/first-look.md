> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# First look in detail

## Reading first_pass

- **Monthly figures:** income, spending, debt payments, and net, over the
  full months the records cover. Spending counts purchases and bills from
  cash and cards, interest and fees included; debt payments and moves between
  their own accounts are not spending. Quote the figures as returned, with
  the months they cover.
- **Accounts:** each with its balance and, for cards and loans, rate,
  minimum, and due date where known. A missing term is unknown, not zero.
- **Recurring:** series Candor detected, with amounts and next dates.
  Candidates are guesses until confirmed (see `candor-sort-transactions`).

Each figure has a matching read in `next_actions` when you need the records
behind it, for example the largest category in a month or a card's terms.

## When the picture is partial

- **A sync is filling in:** do the first look on what has landed and say
  which accounts are still coming.
- **Some accounts are missing:** name what the picture cannot see, such as a
  partner's card or a retirement account, and offer to add it from a
  statement or export; connecting it is their choice on the web.
- **Balances only:** say what transaction history would answer (where the
  money goes, what repeats).
- **Every account excluded:** check inclusion with
  `candor_get({"operation":"accounts.policy.get","reason":"Check whether the account is included","args":{"account_identity_id":"ACCOUNT_ID"}})` before anything else.
- **Accounts kept by hand:** say how far each one's records reach
  (`records_through` in the opening's coverage) and read nothing after that
  date as a change in their money.

## What the household answers unlock

Candor's review weighs adviser checks against these answers. The
retirement and health questions use US terms; outside the US, read them as
the local equivalents. Use them to
choose what to look at, and ask only about the ones they skipped when it
changes what you would look at next.

| Answer | What it points you to |
| --- | --- |
| Self-employed or both | Quarterly taxes, retirement accounts for the self-employed, mixing business and personal money |
| Dependents | Life and disability coverage, an emergency fund that covers them |
| Upcoming changes | The goal behind the change (a home, a child, a move, retiring) |
| Age range | Retirement pace, catch-up contributions |
| Housing | Mortgage rate and payoff, renter's coverage |
| Contributes less than the match | An uncaptured employer match |
| High-deductible plan with an HSA | HSA contributions and receipts |

## Their starting point

The starting point they chose at signup arrives first in `agent_context`
with their wording. Lead the first look toward it. If they edit or drop it,
update or resolve that same note rather than adding another.
