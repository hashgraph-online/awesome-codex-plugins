---
title: Error Prevention & Recovery
impact: HIGH
tags: errors, undo, validation, forms, destructive-actions, user-control
---

**Rule**: Make errors hard to make and easy to undo. Prefer constraints and undo over warnings; give every flow a visible way out; accept input in any reasonable format.

**Evidence**: Nielsen's usability heuristics #3 (user control and freedom), #5 (error prevention), and #9 (help users recognise, diagnose, and recover from errors). Norman, *The Design of Everyday Things* (2013) — slips (right goal, wrong action) need constraints; mistakes (wrong goal) need clearer information. Raskin, *The Humane Interface* (2000) — confirmations become habitual and get clicked through; undo protects better. Postel's robustness principle (RFC 761, 1980), applied to input: be liberal in what you accept.

### When Building

- **Constrain instead of validate** — pickers for dates, steppers for quantities, disabled states for impossible actions (with a reason shown)
- **Undo over confirm** — archive, delete, and move with an Undo snackbar/toast; keep a confirmation dialog only for truly irreversible actions (account deletion, payments, sending to others)
- **Confirmations that work** — name the consequence and the object ("Delete 'Q3 Report'? This can't be undone"), make the destructive button say what it does ("Delete report"), and never default focus to it
- **Escape hatches** — every modal, sheet, and multi-step flow has a visible Cancel/Close and back; leaving keeps entered data or asks once
- **Liberal input** — accept spaces and dashes in card and phone numbers, any case in emails and codes, pasted values with stray whitespace; normalise in code
- **Errors that help** — next to the field, in plain words, with the fix (`rules/microcopy.md`); keep everything the user already entered

### When Auditing

- Destructive actions without undo or confirmation; confirmations on trivial, reversible actions (they train click-through)
- Flows with no cancel or back, or that lose input on back
- Inputs that reject valid formats (`pattern` attributes, strict regexes on phone, postcode, card)
- Errors that clear the form, appear only at the top, or show codes instead of fixes

### Incorrect

```tsx
if (!/^\d{16}$/.test(card)) setError("Invalid card number");
```

### Correct

```tsx
const digits = card.replace(/[\s-]/g, "");
if (!/^\d{12,19}$/.test(digits)) setError("Enter the 12–19 digits on the front of your card");
```

### Why This Matters

Most "user errors" are design errors. Each one costs a support ticket, an abandoned flow, or lost data — and the user blames themselves, then the product.

### Alternatives

Strict formats are right where ambiguity is dangerous (an amount field must not guess the decimal separator; a legal name should not be "corrected"). High-stakes, irreversible actions earn friction — typing the project name to delete it is a deliberate speed bump, not a bug.
