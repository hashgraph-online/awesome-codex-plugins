# Configuration or infrastructure — items that change resolved config, a plan, or how a change is undone

## When it applies

An item that changes config, a plan, a manifest, or the way that change is undone.

## Evidence lines

- The resolved config diff, the plan or dry-run output, and how the change is undone.

## How to generate

Save the resolved config diff, the plan or dry-run output, and the steps that undo the change. Write them into `plan.txt` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

The diff is the resolved config, not the unrendered source. The plan or dry-run output is from the command the item names. The undo steps reverse this change.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the diff, the plan, or the undo steps. No rendered secret that the source had kept out of the file.
