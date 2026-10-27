---
title: Microcopy
impact: HIGH
tags: copy, labels, errors, empty-states, ux-writing, buttons
---

**Rule**: Words are interface. Buttons say what happens, errors say how to fix the problem, and everything uses the user's language, not the system's.

**Evidence**: Nielsen's heuristics #2 (match between system and the real world) and #9 (help users recognise, diagnose, and recover from errors). NN/g's error-message guidelines — visible, specific, constructive, and polite. The GOV.UK content design guidance — plain language, front-loaded words, written for the user's task.

### When Building

- **Buttons are verbs with objects** — "Save changes", "Send invoice", "Delete project" — not "OK", "Submit", "Yes"
- **Dialog buttons repeat the decision** — "Discard draft?" → "Discard" / "Keep editing", so the choice reads without the question
- **Errors**: what happened, in plain words, and what to do — next to the problem, without blame. "That email is already registered — sign in instead?" not "Error 409" or "Invalid input"
- **Empty states**: what will appear here, why it is empty, and the one action that fills it
- **Labels over placeholders** — placeholders disappear on typing; examples go in hint text
- **The user's words** — "Couldn't connect. Check your internet and try again." not "Network request failed"; "Your plan" not "Subscription entity"
- **Front-load** — put the meaningful word first in headings, list items, and notifications (`rules/scanning.md`)
- **Consistent terms** — one word per concept across the product (`rules/jakobs-law.md`)

### When Auditing

- Generic labels: OK, Submit, Yes/No, Click here, Learn more (with no object)
- Raw errors: status codes, exception messages, "Something went wrong" with no next step
- Empty screens with no explanation or action
- Placeholder-only inputs; jargon and internal names in the UI

### Incorrect

```tsx
<Alert title="Error" message={err.message} buttons={[{ text: "OK" }]} />
```

### Correct

```tsx
<Alert
  title="Payment didn't go through"
  message="Your card was declined. Try another card or contact your bank."
  buttons={[{ text: "Use another card", onPress: changeCard }, { text: "Cancel", style: "cancel" }]}
/>
```

### Why This Matters

Users read labels to decide what to do and error messages to recover. Vague words cause hesitation, wrong choices, and abandoned flows; clear words do the work of a tutorial.

### Alternatives

Universally understood short labels ("Cancel", "Close", "Done", "Next") are fine where the context makes the object obvious. Brand voice and playfulness belong in low-stakes moments — never in errors, payments, or anything destructive.
