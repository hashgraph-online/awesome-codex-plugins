---
case: book-B8
description: Use when a long piece needs different kinds of pages: prose, a diagram, a table that reads best as a web page.
---

# Mixed pages

Shapes: book with note and html pages.

```sh
echo "What changed in the cache, and why." | stickypane note write review/cache/01-overview --open
printf '```mermaid\nflowchart LR\n  api --> cache --> db\n```\n' | stickypane note write review/cache/02-shape
printf '<table><tr><th>case</th><th>ms</th></tr><tr><td>warm</td><td>12</td></tr></table>\n' | stickypane note write review/cache/03-numbers.html
stickypane page list review/cache
```

A page takes any shape a note can. The terminal shows an html page as
text only, so say its key number in a note page too.

Done when: `page list` shows the pages in order, and every number on an
html page is also in words on a note page.
