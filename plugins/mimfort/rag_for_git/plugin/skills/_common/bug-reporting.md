**Defect of reviewer itself?** A tool breaking its documented contract, an impossible skill step,
a failed stated invariant, or a `reviewer/*` frame in a traceback — tell the user in one line and
offer the `report-bug` skill. Stay silent about everything else: unavailable Postgres/Neo4j,
missing keys, a stale index, rate limits, VCS errors, the user's own tests or git conflicts,
permission denials. Never publish yourself — only `report_bug`, with an explicit human approval,
never in headless or background runs.

When a reviewer result looks unexpected and the client has no automatic diagnostic hook,
call `diagnose_tool_result(tool, response)` if the MCP server exposes it. Pass the logical
reviewer tool name and the returned error/status envelope or traceback as text. A
`suspected_defect` result carries the failure class and a deduplication signature. Use it to
decide whether to offer the report-bug skill. The diagnostic call never publishes a report.
