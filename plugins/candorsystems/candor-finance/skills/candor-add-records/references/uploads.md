> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Uploads

An upload brings a whole file into Candor once. Candor reads every row; you
read what it found, write a small mapping, preview it over every row, and
apply. Nothing lands in the records until you apply, and Candor splits the
rows into import batches by account and period itself.

Use an upload for every export file the person has, of any size (a bank
CSV, another finance app's export), for any file the person already put in
Candor, and for a monthly statement file Candor has seen before. The person
drops it into Candor through the link, so its rows never pass through the
chat; a CSV they already attached in the chat goes through the link too. When
they have no export yet, Candor's guide at
`https://candor.money/how-to-export-your-transactions` shows how to download
one from a bank or another app. Candor reads delimited text (CSV, TSV, TXT), QIF, and a ZIP of up to
five of those, up to 20 MB. A PDF statement or screenshot is never an
upload: one already in the chat is read there and imported inline, as you
would rows pasted into the chat.

## Get the file in

- **The person already dropped it** on the Accounts page: the opening raises
  it as `uploads.waiting`, or they paste a request naming the upload ids.
  Go straight to reading it.
- **The person has the file:** create an upload and give them its
  `link_url` in the same reply, saying to open it on the device that has the
  file and drop the file there. Create it now even if they are on another
  device: a link costs nothing, and if it runs out (it works once, for 30
  minutes) you create another when they are ready. Then wait for them to say
  it is in; the response's `next_actions` say what to read next.

```text
candor_write({
  "operation": "uploads.create",
  "reason": "Get the person's export into Candor"
})
```

  If the link ran out, they can drop the file on the Accounts page instead,
  and `candor_get({"operation":"uploads.list","reason":"Find the upload the person dropped"})`
  shows it.
- **You have the file and can run a shell command:** ask for the upload URL
  and send the file with an HTTP PUT; no link is needed. With the Candor CLI,
  the uploads create command given the export's path as its file option does
  both steps at once.

```text
candor_write({
  "operation": "uploads.create",
  "reason": "Send the export the person shared",
  "args": {
    "direct": true
  }
})
curl -T EXPORT.csv "UPLOAD_URL"
```

## Read what Candor found

```text
candor_get({
  "operation": "uploads.get",
  "reason": "Read what Candor found in the file",
  "args": {
    "upload_id": "UPLOAD_ID"
  }
})
candor_get({
  "operation": "uploads.rows",
  "reason": "Read the file's rows",
  "args": {
    "upload_id": "UPLOAD_ID",
    "from_line": 1,
    "limit": 200
  }
})
```

The upload carries the header, the preamble lines above it (an account
name, a masked number, a statement period), the first and last rows, a
profile of each column (blanks, the most frequent values, date and amount
ranges), the accounts found with their rows, dates, and any closing balance,
and `likely_matches`: accounts already in Candor with the same last four or
name, and whether each is connected. `reader.guess.mapping` is a mapping as
far as the file can tell, with each field marked `detected`, `preset`,
`saved_mapping`, or `ambiguous`. A Monarch, Copilot, YNAB, Mint, or Quicken
export is recognized by its header, so the guess is nearly complete.

The column profiles show totals rows, type values, pending values, and
account values without paging the whole file; page rows where you need to
see more. A file that is not transactions (YNAB's plan file, say) says so in
`reader.not_transactions`: discard it and tell the person what to export
instead.

## Write the mapping

Start from `reader.guess.mapping` and add what the file cannot say. For
every field, `candor_schema({"operation":"uploads.preview"})`.

- **Amount:** one signed column with `money_out_is` (`negative` or
  `positive`), `debit` and `credit` columns, or an amount column with a type
  column and the type values that mean money out. Check one purchase you can
  recognize: in Candor it must read as money out.
- **Accounts:** each value of the account column (or one entry with no
  `value` when there is none) goes to an existing account by
  `source_account_id`, to a new account under a `handle` with its
  `new_account` details, or to `skip`. Every value is mapped or skipped.
- **Balance:** a new account needs one: a running-balance column, the
  statement's `closing_balance` with its date, or an `opening_balance`. On a
  card or loan, a balance is what is owed, as a positive number.
- **Period:** `period.through` is the last day the file covers: the
  statement's closing date or the export's last full day, and the last
  row's date only when nothing says the file runs later. A period the file
  states (`layout.period_line`) sets both ends, and days inside it with no
  rows were quiet: apply through it without asking. A period counts as
  complete by default, so Candor reads a bill missing from it as missed;
  set `complete: false` for a filtered or partial export.
- **Rows to leave out:** `filters` drop rows whose cell `equals` or
  `starts_with` a value (opening, total, and closing rows); `fixes` skip or
  correct one line. Pending rows, named through `columns.status`, are always
  left out until they post.
- **Category and role:** map the file's category column; Candor keeps the
  label as the person had it and reads common ones into income, transfers,
  and debt payments. When another column says what a row is (Copilot's
  `type` of `income` or `internal transfer`, YNAB's `Transfer : Savings`
  payee), `columns.role` maps its exact values or prefixes to roles, so
  those rows count right from the start; the Copilot, YNAB, and Quicken
  presets already map theirs.
- **Layout:** leave it to the reader unless it guessed wrong; set
  `date_format` when the dates read more than one way.

A bank CSV the person downloaded, with a preamble, `Debit` and `Credit`
columns, and a running balance, for their checking account already in
Candor. The reader finds the header on line 4, the dates, and the columns;
the mapping adds the account, the period, and the lines a later statement
will repeat:

```text
Account: Everyday Checking ****4821
Statement period: 08/01/2026 to 10/31/2026

Posting Date,Description,Debit,Credit,Balance
10/31/2026,ONLINE TRANSFER TO SAVINGS 9930,500.00,,2318.44
10/30/2026,HARBOR CO PAYROLL,,2866.00,2818.44
```

```text
candor_write({
  "operation": "uploads.preview",
  "reason": "Preview the checking export against its account",
  "args": {
    "upload_id": "UPLOAD_ID"
  },
  "input": {
    "mapping": {
      "layout": {
        "period_line": 2
      },
      "columns": {
        "date": "Posting Date",
        "description": "Description",
        "amount": {
          "debit": "Debit",
          "credit": "Credit"
        },
        "running_balance": {
          "column": "Balance"
        }
      },
      "accounts": [
        {
          "source_account_id": "SOURCE_ACCOUNT_ID"
        }
      ],
      "period": {
        "through": "2026-10-31"
      },
      "match_line": 1,
      "save_as": "Everyday Checking"
    }
  }
})
```

`match_line` makes next month's statement match this mapping only when its
account line is the same, and `period_line` offers that statement's period
end. A card export that lists purchases as positive and payments as
negative, with no balance column, for a card not in Candor yet. The reader
marks the amount's sign `ambiguous`; the grocery purchase reads positive, so
money out is positive. The person read the October 31 balance off their
statement:

```text
Transaction Date,Description,Category,Amount
10/28/2026,TRADER JOE'S #552,Groceries,54.12
10/15/2026,AUTOMATIC PAYMENT THANK YOU,Payment,-1240.00
```

```text
candor_write({
  "operation": "uploads.preview",
  "reason": "Preview the card export as a new account",
  "args": {
    "upload_id": "UPLOAD_ID"
  },
  "input": {
    "mapping": {
      "columns": {
        "date": "Transaction Date",
        "description": "Description",
        "category": "Category",
        "amount": {
          "signed": "Amount",
          "money_out_is": "positive"
        }
      },
      "accounts": [
        {
          "handle": "card",
          "new_account": {
            "display_name": "Sapphire card",
            "institution_name": "Chase",
            "type": "credit",
            "subtype": "credit card",
            "currency": "USD"
          },
          "closing_balance": {
            "amount": "1873.40",
            "as_of": "2026-10-31"
          }
        }
      ],
      "period": {
        "through": "2026-10-31"
      },
      "save_as": "Sapphire card"
    }
  }
})
```

## Preview until the checks agree

Each preview saves a new revision and changes no records. Per account it
returns rows read, the period, each month's rows and money in and out, the
running-balance check (`holds`, or `breaks` at the first bad line with what
it expected), the file's closing balance against Candor's on that date, rows
already in Candor (`duplicate`, `covered` by a bank connection,
`period_covered` and `import_overlap` inside an earlier import), near
matches (`conflict`), how its rows will count (`roles`, with the categories
no role reads in `unknown_roles`), and the batches it would land with
whether each counts as complete. With no balance column, a `balance_file`
is checked the same way as a running balance: each of its dates must follow
from the one before by the rows between. Errors such as `date_format_ambiguous`, `through_required`, or
`new_account_needs_balance` block apply until the mapping settles them.

Before applying:

- The running-balance check holds. A break at the first row usually means a
  flipped sign or the wrong column; fix the mapping rather than applying past
  it.
- The months and money in and out are worked out from the file's own rows,
  so they test the mapping: signs, accounts, and the period. Compare them
  with what you already hold (a statement's printed totals, records already
  in Candor) when you have it. With no balance column, the balance you
  state anchors the account and the file is the history; a check marked
  `not_checked` has nothing to compare, which is not a failure. Do not ask
  the person to reproduce totals from their old app or bank.
- Every line not read is fixed, skipped, or left for an inline slice.
- A `conflict` that is the same purchase as a record Candor has gets a skip
  fix. Rows inside an earlier import stay skipped unless that import was
  partial and the rows are truly missing; then that account entry takes
  `overlap: "import"`.
- `rows_end_early` means an account's rows stop more than 35 days before
  a `through` the file does not state: a closed account or a short
  download. Find out which before reading the quiet as real.

Preview again with each correction and apply the revision you checked.

## Ask only what the file cannot answer

Candor never applies a `likely_matches` entry; you decide. When a file
account could be one already in Candor (most often a connected one with the same
last four) and nothing in the file or records settles it, ask that one
question. When dates read more than one way, `date_candidates` gives the
file's order and range under each, and the preamble's period often decides;
ask only when neither does. A new account's balance the file does not state
is also the person's to give. When a target is marked `header_only`, confirm
the account from the preamble before applying. Otherwise ask only when a
check breaks or differs and the file cannot explain it. Write the mapping,
preview it, and apply what the request covers without checking in first.

## What a mapping cannot express

A mapping reads one table of rows. Accounts in sections under their own
heading lines, descriptions that wrap onto a second line, split lines given
as extra rows, and holdings files do not fit. Read those rows with
`uploads.rows`, leave them out of the mapping with filters or fixes, and
send them as inline imports (steps 3 to 5 of the workflow) before applying
the upload, so each period is complete when its coverage lands. A QIF split
record comes in at its total; add its lines with `transactions.split.set`
when the person wants them.

## Apply, check, and report

```text
candor_write({
  "operation": "uploads.apply",
  "reason": "Bring the checked export into Candor",
  "args": {
    "upload_id": "UPLOAD_ID",
    "preview_revision": "PREVIEW_REVISION"
  }
})
```

New accounts are created first, then each batch lands. The response waits
up to 40 seconds; a long history keeps going in the background, and one
`uploads.get` of it waits up to 40 seconds more, so read it then instead of
polling. An apply that stops partway resumes from the next batch with the
same revision. The response names any filtered or fixed lines that did not
come in, and `apply.accounts` gives each account's rows created and skipped,
its balance, and `records_through`: compare those with the file and
spot-check one month of one account rather than reading each account or
the history back.
Tell the person in their terms:
which accounts, what dates, how many transactions came in, how many were
already there and why (a bank connection covers those days, an earlier
statement holds them), the closing balances, and anything left out (pending
rows, unread lines), with no ids. When an earlier file left rows out as pending, say
whether they have now come in at their posted amounts.

## Next month's file

Applying saves the mapping. When a later file from the same source arrives,
Candor previews it with that mapping at once, and the upload waits with
`through_required`, plus `balance_required` when the format has no balance
column. `through_candidates` holds the last row's date and any period from
the preamble, and `opening_balance_candidate` holds Candor's balance on the
day before the file starts or, when the file overlaps what Candor holds, on
the last day those records reach; it goes in as `opening_balance` either
way. Take the preview's
`summary.mapping`, add `period.through` and the balance (the candidate, or
the statement's closing balance), and preview it once more; applying a
changed mapping updates the saved one. With two saved mappings for one
format, pick one by its `mapping_id`:

```text
candor_write({
  "operation": "uploads.preview",
  "reason": "Preview the new statement with its saved mapping",
  "args": {
    "upload_id": "UPLOAD_ID",
    "mapping_id": "MAPPING_ID"
  }
})
candor_get({
  "operation": "uploads.mappings.list",
  "reason": "Read the saved mappings"
})
candor_write({
  "operation": "uploads.mappings.remove",
  "reason": "Remove the mapping the person no longer uses",
  "args": {
    "mapping_id": "MAPPING_ID"
  }
})
```

## Discard and revert

```text
candor_write({
  "operation": "uploads.discard",
  "reason": "Throw away the file that is not transactions",
  "args": {
    "upload_id": "UPLOAD_ID"
  }
})
candor_write({
  "operation": "uploads.revert",
  "reason": "Undo the upload that landed on the wrong account",
  "args": {
    "upload_id": "UPLOAD_ID"
  }
})
```

Discard throws away an upload with nothing landed, and its file. The file of
an applied upload stays for 14 days in case a slice or a redo needs it;
`file_only` deletes just the file and keeps the records. Revert undoes
every batch an upload landed, including the accounts it created; preview a
corrected mapping and apply again to redo it. `imports.revert` undoes one
batch alone.
