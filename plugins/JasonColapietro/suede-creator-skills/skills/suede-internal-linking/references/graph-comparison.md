# Graph comparison example

The example below uses fictitious pages and counts. Keep matched URL cohorts,
same crawl limits, redirect-following rules, and the same entry point for both
observations.

| Destination | Before contextual links | Proposed change | Post-change check |
|---|---:|---|---|
| /services/migration | 0 | Add a relevant next step from /guides/site-moves | At least one rendered contextual link; expected final canonical 200 |
| /support/migration | 4 | Replace a deprecated path on /docs/setup | View /docs/setup while signed out; no extra hop; no lost link |
| /account/requests | 0 | No SEO intervention | Deliberately restricted; do not treat as orphan |

## Collect useful evidence

Keep separate lists for eligible pages with no verified inbound edges, pages
not reached because of crawl limits, and intentionally excluded destinations.
For every contextual link capture source heading, exact visible anchor,
destination canonical, and where you verified the link built and rendered.
Use the shortest crawler path as a comparative diagnostic. It is not a promise
a human will take that path or a ranking factor with a known fixed weight.
