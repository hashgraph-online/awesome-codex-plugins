---
case: html-H4
description: Use when a tool already wrote a report (coverage, test results, a profile) as a web page, and the user should see it.
---

# A page a tool made

Shapes: html, note.

```sh
go test -coverprofile=cover.out ./... && go tool cover -html=cover.out -o coverage.html
stickypane note show coverage.html
echo "Coverage 81.4%, down from 83.0%: store/ lost tests." | stickypane note write coverage-summary --open
```

Show the file the tool wrote; do not write a second page of the same
numbers. The terminal shows the page's text only, and the desktop app
draws it: put the one number that matters in a note beside it.

Done when: `stickypane index` lists `coverage.html` and the summary
note, and the summary's number is the one the tool printed.
