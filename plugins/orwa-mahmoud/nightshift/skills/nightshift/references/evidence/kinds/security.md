# Security — items that change a scan result or how a finding is handled

## When it applies

An item that changes what a scan finds, or how a finding is disposed.

## Evidence lines

- The scan command and its output, and each finding's disposition: fixed, accepted with a reason, or not applicable.

## How to generate

Run the scan command the item names and save the command and its output. For each finding, record one disposition: fixed, accepted with a reason, or not applicable. Write that into `scan.txt` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

The command and the output are both in the file. Every finding in the output has one of those three dispositions, and an accepted finding has its reason next to it.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the scan output. Redact a credential, a cookie, or a real person's data before the file is written.
