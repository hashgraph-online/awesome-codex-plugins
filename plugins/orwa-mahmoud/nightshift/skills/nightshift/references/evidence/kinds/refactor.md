# Refactor — items that move code and leave the behaviour the same

## When it applies

An item that moves or restructures code and leaves the behaviour the same.

## Evidence lines

- What moved where, what stayed behaviour-identical, and how that was shown: the unchanged tests, a before/after output diff, or both.

## How to generate

Write what moved where, what stayed behaviour-identical, and how that was shown. The showing is the unchanged tests, a before/after output diff, or both. When there is a diff, save it as `behaviour.diff` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`. The note itself belongs in the receipt.

## How to verify

The note names the move and the behaviour that stayed. It points at the tests that still pass or at the diff, and the diff shows the same result before and after.

## Never

No secrets, tokens, or personal data in the diff or the note. No claim that behaviour stayed the same without the tests or the diff that show it.
