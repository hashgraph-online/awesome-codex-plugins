---
case: book-B7
description: Use when a plan has parts that each need a page (a migration, a rewrite), and its progress should sit beside it.
---

# A migration in pages

Shapes: book, checklist.

```sh
echo "Why we move from v1 to v2, and what stays." | stickypane note write migration/plan/01-why --open
stickypane page add migration/plan "02 Order of the steps"
stickypane page add migration/plan "03 How to roll back"
stickypane todo add migration/progress "move the readers"
stickypane page list migration/plan
```

A book is a folder in a tab: here the tab `migration`, the book `plan`.
`page add` makes an empty page named after its words; write it with
`stickypane note write migration/plan/<page>`. The progress is a
checklist in the same tab, one line per step of page 02.

Done when: `stickypane page list migration/plan` lists every page, and
the checklist has a line for each step page 02 names.
