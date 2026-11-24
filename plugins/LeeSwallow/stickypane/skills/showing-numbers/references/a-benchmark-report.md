---
case: html-H2
description: Use when a measurement gives many numbers at once (each case, before and after, the spread) that read best as one table.
---

# A benchmark report

Shapes: html, note.

```sh
stickypane note write bench.html --open <<'EOF'
<h1>Price lookup, 10 runs each</h1>
<table>
<tr><th>case</th><th>before</th><th>after</th><th>spread</th></tr>
<tr><td>cold</td><td>910 ms</td><td>880 ms</td><td>±40</td></tr>
<tr><td>warm</td><td>900 ms</td><td>12 ms</td><td>±2</td></tr>
</table>
EOF
echo "Warm lookups 900 → 12 ms (10 runs); cold ones unchanged." | stickypane note write bench-summary --open
```

A page for the table, read once; a chart is for one number over time.
Give each number its run count and spread. The terminal shows the
page as text, so the result also goes in a one-line note.

Done when: every number in the table comes from a run you made, with
the run count stated.
