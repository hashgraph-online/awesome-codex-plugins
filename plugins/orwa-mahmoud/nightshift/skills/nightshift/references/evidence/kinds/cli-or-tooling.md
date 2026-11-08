# CLI or tooling — items that change a command a person runs

## When it applies

An item that changes a command a person runs, including the error that command shows.

## Evidence lines

- The command run and its output before and after, including the error a user sees.

## How to generate

Run the command before the change and after it. Keep stdout and stderr, including the error a user sees. Write the command and both outputs into `command.txt` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

The file has the command, the before output, and the after output. The error a user sees is the error text, not a description of it.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the command line or its output. No live token passed as an argument.
