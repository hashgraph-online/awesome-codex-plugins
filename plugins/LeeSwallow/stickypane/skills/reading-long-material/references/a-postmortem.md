---
case: book-B5
description: Use when something broke (an outage, a bad release) and the user wants it written up once it is fixed.
---

# A postmortem

Shapes: book.

```sh
echo "Checkout failed for 42 minutes on 3 Oct; fixed by a rollback." | stickypane note write incidents/checkout/01-summary --open
stickypane page add incidents/checkout "02 Timeline"
stickypane page add incidents/checkout "03 Cause"
stickypane page add incidents/checkout "04 What we change"
```

Four pages: summary, timeline, cause, what changes. The timeline takes
its times from logs, not memory. Blame no one; name the parts that
failed.

Done when: every time in the timeline comes from a log, and every item
in "What we change" can be checked off.
