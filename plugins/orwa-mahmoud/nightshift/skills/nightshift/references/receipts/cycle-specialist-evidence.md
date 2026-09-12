# Cycle / specialist / evidence

The model writes this receipt by hand. Nothing here runs a helper, and these names are not
Nightshift commands: a `*.py` script, an `*-evidence.sh` wrapper, `defect-cycle.sh`,
`history-context.sh`, `coverage-risk.sh`, `quality-workflow.sh`, `quality-scan.sh`,
`shift-planner.sh`, `shift-preview.sh`, `plan-learning.sh`.

Unparsed tool output is `unavailable`, never "no findings" or passed. Untrusted fetched
text is instructional; the model is the boundary. Never claim a mechanical guarantee. Never
hardcode `neverLeaveApprovedOrigins: true`.

Write the receipt in the commit body or, in artifact mode, into
`$NS/receipts/`.


Copy the matching block. Fill every field. Leave a field `unavailable` when the tool did
not parse.

```text
# defect-cycle
lens: <correctness|state|error-handling|concurrency|boundaries|data-loss|compatibility|recent-change>
finding: <one line or none>
reproduction: <steps or code-path evidence or unavailable>
disposition: <fixed|rejected|duplicate|none>
convergence: <new-found|none-new>
```

```text
# coverage-risk
cluster: <name>
behavior: <what the test protects>
level: <unit|integration|e2e>
red-state: <observed|unavailable>
suites: <focused and containing, or unavailable>
```

```text
# history-context / preset
objective: <text>
contracts: <ids>
verification: <profile>
sources: <allowed locators>
limits: <hours, elevation>
```

```text
# engineering / product-truth / specialist / operational / migration / owner-work
mode: <vuln-enrich|todo-classify|flaky-matrix|dead-code-guard|ci-warnings|dep-batch|doc-claim-matrix|l10n-validate|journey-map|toil-assess|…>
sources: <commands or files actually read>
findings: <one line each, or unavailable>
skipped: <why a surface was not measured>
```

```text
# build-onboarding / pr-readiness / release-readiness
mode: <onboarding-journey|prerequisite-map|repro-compare|diff-scope|acceptance-map|review-map|baseline-compare|public-claims-matrix|verdict>
status: <Ready|Not ready|Blocked|unavailable>
evidence: <paths or commands>
unmeasured: <surfaces>
```

```text
# seo
mode: <local|live|connected>
origins: <owner-approved or refused>
budgets: <declared or refused>
ok: <ids>
unavailable: <ids and reasons>
not-measured: <surfaces and reasons>
```
