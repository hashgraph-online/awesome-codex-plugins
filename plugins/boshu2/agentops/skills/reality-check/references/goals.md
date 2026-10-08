# Goal measurement

Loaded by [Reality Check](../SKILL.md) when the caller asks to measure declared
goals.

Inspect the declared goals source; prefer `GOALS.md` when it and legacy YAML
both exist (`ao goals` auto-detects `GOALS.md` first). Preserve directive and
gate identities and report each executable check with its actual outcome. Run
the requested `ao goals` command once: `measure --json`, `validate --json`,
`drift`, `history`, `export`, `meta --json`, `scenarios` or `render`.

These commands do not edit the goals source, but `measure`, `drift` and
`export` may write best-effort derived snapshots under
`.agents/ao/goals/baselines/`. `render --out <file>` writes a caller-selected
spec; never target the goals source or another non-derived file. Use stdout
when no output file is requested.

Return the command, exit code, goal-level results, aggregate measurement,
missing evidence and checked/not-checked scope. Do not add, remove, prioritize,
migrate or repair goals, or turn a measurement gap into assigned work.
