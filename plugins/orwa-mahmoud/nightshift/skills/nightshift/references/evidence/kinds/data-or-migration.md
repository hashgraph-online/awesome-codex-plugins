# Data or migration — items that move, rewrite, or recount stored records

## When it applies

An item that migrates, rewrites, or recounts stored records.

## Evidence lines

- Row or record counts before and after, the migration's own output, and the rollback command.

## How to generate

Count the rows or records before the migration and after it. Keep the migration's own output. Write the counts, that output, and the rollback command into `migration.txt` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

Both counts are present and they are counts of the same set. The output is the migration's, not a paraphrase. The rollback command is the one that undoes this migration.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the counts, the migration output, or the rollback command. No dump of live rows.
