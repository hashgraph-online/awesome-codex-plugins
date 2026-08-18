**Defect of reviewer itself?** A tool breaking its documented contract, an impossible skill step,
a failed stated invariant, or a `reviewer/*` frame in a traceback — tell the user in one line and
offer the `report-bug` skill. Stay silent about everything else: unavailable Postgres/Neo4j,
missing keys, a stale index, rate limits, VCS errors, the user's own tests or git conflicts,
permission denials. Never publish yourself — only `report_bug`, with an explicit human approval,
never in headless or background runs.
