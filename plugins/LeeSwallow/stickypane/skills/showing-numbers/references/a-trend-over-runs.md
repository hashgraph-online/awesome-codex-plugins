---
case: chart-C5
description: Use when you run something many times (a flaky test, a benchmark) and the user should see whether it gets better or worse.
---

# A trend over runs

Shapes: chart.

```sh
stickypane note write flaky --type chart --opt view=spark --open </dev/null
stickypane chart set flaky run-01 4
stickypane chart set flaky run-02 3
stickypane chart set flaky run-03 1
```

One label per run, in order, so the line reads left to right. Put the
number of tries behind each value in the title (`flaky of 50 runs`):
4 of 50 and 4 of 5 are not the same.

Done when: the chart has one value per run you made, and its title says
how many tries each value counts.
