> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Moving from another finance app

Someone leaving Monarch, Copilot, YNAB, Mint, Quicken, or a spreadsheet can
bring their history with them through you. The export comes in as an upload
(see the uploads reference): Candor reads every row, you map it once and
preview it, and Candor splits it into batches by account and period.

## Get the export

Ask for a CSV of all transactions over the longest range the app offers.
These apps put it in their settings or on the transactions list; their help
pages have the current steps, since menus move. Candor's guide at
`https://candor.money/how-to-export-your-transactions` walks the person
through downloading one from a bank or another app; give them that link when
they are not sure where to look.

- **Monarch:** a transactions CSV from its data settings, plus each
  account's balance history if they want past balances. One download holds
  at most 10,000 rows, so a long history is several downloads by date range,
  all dropped together.
- **Copilot:** a transactions CSV from its settings.
- **YNAB:** the budget export, a ZIP. Each file inside becomes its own
  upload: the register holds the transactions, and the plan is not
  transactions, so discard its upload.
- **Mint:** closed in 2024, so use a CSV the person saved before then.
- **Quicken:** a QIF export, or a CSV from a transaction report.

The person drops the files on Candor's Accounts page, or opens the link you
give them on the computer that has them. Budgets and goals from the old app
are not imported: rebuild them with the person in `candor-budget` and
`candor-plan-a-goal`.

## Map the first file

Candor recognizes these apps' exports, so `reader.guess` already holds the
columns, signs, and dates. What you add:

- **Accounts:** each account in the file goes to one already in Candor or to
  a new account named as the person knows it, in its own currency. These
  apps export one currency and write no currency column: use the currency
  of the person's accounts in Candor, or the amounts' symbol, and ask only
  when those disagree. Read `likely_matches`; ask only when a file account
  could be a connected one and nothing settles it. Days a bank connection already covers are
  skipped, so older history from before the connection still comes in.
- **Balances:** each new account needs one. Monarch's balance history comes
  in as its own upload, named in the mapping's `balance_file`. Otherwise
  state each account's balance on the export's last day as its
  `closing_balance`, from the old app's account history or a statement.
- **Period:** `through` is the export's last full day, not today. A full,
  unfiltered export counts as complete; set `complete: false` for a filtered
  one.
- **Rows to ask about:** rows the old app hid or excluded, and balance
  adjustments it invented. Ask before importing those.
- **Split rows:** a split written as separate rows, each with its own amount
  and no total row beside them (YNAB's), imports each row once as it is. A
  split written as a total plus its lines counts twice, so keep the total
  and leave the lines out of the mapping (the uploads reference has the
  way).

Preview, then read each account's rows, months, and money in and out: the
export is the old app's own record, so these test your mapping (signs,
accounts, period), not the file. A stated closing balance anchors an export
with no balance column. Apply once the preview's checks hold; ask the person
only for a fact the file lacks or about a check that breaks, never for the
old app's totals.

## The next files

Map each further download onto the accounts the first one created. Once
the first applies, its `next_actions` offer each waiting download with the
same columns a preview carrying the mapping just applied, already pointed at
those accounts: add that file's `period.through` and send it. Rows repeated
on a shared boundary day are skipped as duplicates, so each row lands once.

## Categories and cash-flow roles

Each preview says how the rows will count: `roles` per account, and in
`unknown_roles` the categories (or blank ones) whose rows no role reads.
Common labels such as Paychecks, Transfer, and Credit Card Payment already
read right, and so do rows a role column states, so leave those alone.
After the history lands, give a role to what `unknown_roles` listed, and to
any category the person counts differently, so budgets and Candor's review
count each row by what it is. One rule per category covers every
row that carries it, past and future:

```text
candor_query({
  "dataset": "categories",
  "reason": "Read the categories the old app used",
  "filters": {
    "since": "START",
    "until": "END"
  }
})
candor_write({
  "operation": "rules.create",
  "reason": "Count the old app's paychecks as income",
  "args": {
    "name": "Paychecks are income",
    "current_category": "Paychecks",
    "set_cashflow_role": "income",
    "authority": "agent_verified",
    "basis_reason": "The old app filed these deposits as paychecks."
  }
})
```

Keep the old app's labels unless the person wants new names; a rule that
sets a role leaves the label as it was. Tell the person in a line which
categories you saved rules for and how they now count, past and future
rows alike, and name any label you renamed. `candor-sort-transactions` has
the rest of the method.

## Transfers and card payments

An export lists a move between two accounts on both sides, and a card
payment on both the checking account and the card. Bring both accounts
over, so the payment pairs with the card and neither side counts as
spending or income. When only one side's account came over, give that row a
transfer or debt payment role.

## Once it holds

Tell the person their history is in Candor through the export's last day,
per account, with anything left out. Each new month comes from the next
statement or a fresh export of just the new dates, through the same upload,
which finds its saved mapping.
