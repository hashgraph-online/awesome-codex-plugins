---
case: script-S4
description: Use when a measurement should be run by the user (a benchmark that takes minutes, on their machine), and its result should land in a chart by itself.
---

# A script that charts

Shapes: script, chart.

```sh
stickypane note write bench.sh <<'EOF'
#!/bin/sh
ms=$(go test -run '^$' -bench Lookup ./price | awk '/ns\/op/ {print int($3/1000000)}')
stickypane chart set bench "$(git rev-parse --short HEAD)" "$ms"
EOF
stickypane note show bench.sh
```

The user presses Run; the script measures and writes one value, named
after the commit. Over commits, the chart is the trend.

Done when: after a run, the chart has a value for the current commit,
and the script's `.log` shows the run.
