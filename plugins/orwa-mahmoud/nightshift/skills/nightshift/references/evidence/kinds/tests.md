# Tests — items that add a test, or whose behaviour is shown by one

## When it applies

An item that adds or changes tests, or whose delivery is a behaviour a test now covers.

## Evidence lines

- The tests added, the behaviour each one covers, and the coverage change for the touched files.

## How to generate

Name each test that was added or changed and the behaviour it covers. Record the coverage change for the touched files from the project's own coverage command. Write that list into `tests-added.txt` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.

## How to verify

Every new or changed test is named, each name is paired with the behaviour it covers, and the coverage line is the change for the touched files rather than a repository-wide claim.

```evidence-check
files: *.txt
min: 1
type: text
```

## Never

No secrets, tokens, or personal data in the test name, the fixture, or the coverage log.
