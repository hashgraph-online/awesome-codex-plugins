# Accessibility — items that change how people operate or understand an interface

## When it applies

An item changes keyboard navigation, focus behavior, the accessible name of a control, or how a status change is announced.

## Evidence lines

- A before-and-after transcript for the affected path. Include the starting state, the key sequence, the order of focused controls, and the point where focus returns after dismissal.
- If the item changes a name, role, state, or announcement, record the affected element or spoken output. Name the browser and, for speech, the assistive technology and versions used.

## How to generate

Use the same viewport, sample data and starting state on both revisions. Operate the affected path with the keyboard and record the sequence and outcomes. When the item names a semantic or announcement change, inspect the affected element in the accessibility tree or repeat the path with the named screen reader. Save the observations in `receipts/<NN>-<slug>-<id>/accessibility.md`, with the relevant revision beside each run. Use automation output when the check covers the claimed behavior.

## How to verify

Replay the listed steps against the after revision. Check that focus reaches the intended control and returns to the documented target when the flow closes. For a semantics or announcement change, confirm the observed name, role, state or announcement matches the item's expectation. Record any untested combination with the browser or assistive technology that remains to be checked.

```evidence-check
files: accessibility.md
min: 1
type: text
```

## Never

Use sample data. Exclude credentials and personal data from recordings, transcripts, and accessibility tree exports.
