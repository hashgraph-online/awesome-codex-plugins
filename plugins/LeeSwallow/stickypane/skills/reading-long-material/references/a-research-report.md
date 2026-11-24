---
case: book-B3
description: Use when the user asked you to find something out and the findings run to several pages.
---

# A research report

Shapes: book.

```sh
echo "Answer: yes, with one limit. The three findings and where each comes from follow." | stickypane note write research/queues/01-answer --open
stickypane page add research/queues "02 What each option costs"
stickypane page add research/queues "03 Sources"
stickypane page list research/queues
```

The answer goes on the first page, before the evidence. Each page after
it backs one part of the answer; the last page lists the sources, each
with what it was used for. Mark what you inferred rather than read.

Done when: the first page answers the question in a screen, and every
claim on it points to a page that backs it.
