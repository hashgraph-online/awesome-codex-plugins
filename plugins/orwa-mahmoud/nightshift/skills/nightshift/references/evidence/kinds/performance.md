# Performance — items that change how fast or how heavily something runs

## When it applies

An item that changes speed, size, memory, or the load a command puts on the machine.

## Evidence lines

- The exact command, the machine and its load, before/after figures with units, and the run count behind each figure.

## How to generate

Run the command the item names, on one stated machine, at a stated load, the same number of times before and after. Write the command, the machine, the load, the run count, and the figures with their units into `figures.txt` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

The file names the command, the machine, the load, and the units. Each figure has a run count, and before and after used the same command and the same count.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the log. No production traffic in the sample, and no figure whose command or count is missing.
