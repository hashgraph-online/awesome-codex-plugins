# Split spec format

Each `NN-name/spec.md` names its source and owned `REQ-*` IDs, then gives:

- outcome and measurable acceptance
- scope and non-goals
- dependencies and owned system/data/interface boundary
- test expectations
- material risks, assumptions, rollback, and stop conditions

Near the top, copy its manifest declarations exactly:

```text
Dependencies: <split IDs or none>
Boundary: <exact Owns/boundary cell>
```

Carry only planning facts. Do not copy background, other specs, interview prose,
or a full implementation design.
