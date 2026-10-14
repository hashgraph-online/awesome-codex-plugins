# CLI flow

Load this reference when running Superloopy commands beyond the loop engineer's default path. The completion rules — real artifacts under the active evidence root, `loop finish` with the JSON quality gate artifact — live in `SKILL.md`.

## Basic Flow

```sh
superloopy loop begin --brief "<task>" --mode light --json
superloopy loop create --brief "<task>" --mode light --json
superloopy loop create --brief "<task>" --session-id "<id>" --mode strict --json
superloopy loop create --brief $'@goal: Build\n<story one>\n@goal: Verify\n<story two>' --json
superloopy loop guide --json
superloopy loop trace
superloopy loop report
superloopy loop check
superloopy doctor --comparison-path /path/to/comparison --json
```

`status` is the fastest reorientation command; it returns current counts and the immediate guide.

`create` returns the immediate guide too; follow it with `next` unless you used `begin`.

`begin` already starts the first goal and returns the immediate guide, including the next proof command.

The guide shows the next command, proof target, recorded evidence, proof plan, capture template, and evidence template. It also shows recorded evidence for already-passed criteria with each captured timestamp, a flow checklist for start or resume, record artifact-backed proof, check evidence, and finish with quality gate, unresolved criteria with suggested proof paths, manual evidence templates, plus the trace, report, and check commands for evidence inspection. Capture, evidence, and repair templates include `--notes "<summary>"` so proof rows stay self-documenting.

For the active goal's next unresolved criterion, prove command-backed evidence directly:

```sh
superloopy loop prove -- npm test
```

For explicit criterion targeting, write artifacts under `.superloopy/evidence/` or capture a command transcript:

```sh
superloopy loop capture --goal-id G001 --criterion-id C001 -- npm test
superloopy loop evidence --goal-id G001 --criterion-id C001 --status pass --artifact .superloopy/evidence/<artifact>.txt --notes "<summary>" --json
```

Inspect the evidence trail when reporting progress or looking for missing proof:

```sh
superloopy loop trace
superloopy loop report
```

`trace` and `report` both return the next guide action after showing or writing evidence context, including evidence summary counts and a timestamped timeline from the ledger. Their artifact rows include capture times for already-recorded proof, and timeline rows include manual evidence notes when provided. The report artifact also includes recorded evidence with captured timestamp, an Evidence Summary section, the current next action, proof plan, and suggested artifact paths for criteria still missing proof.

Run the lightweight preflight before finishing:

```sh
superloopy loop check
```

`check` prints an evidence summary with artifact-backed criteria, unresolved, and invalid counts. If it is blocked, use the numbered repair plan: each step names the target artifact, capture command, and manual evidence alternative.

`trace`, `check`, and `report` also surface warnings for commandless manual proof, exhausted worker/auditor attempts, and repeated identical failing proof (`repeated-failing-proof`, also printed by `prove`/`capture`). Warnings do not fail a preflight by themselves, but they are a prompt to prefer command-backed proof or close an inconclusive lane.

Finish in one command after all criteria pass:

```sh
superloopy loop finish --evidence "<summary>" --artifact .superloopy/evidence/gate.json --json
```

For custom gate workflows:

```sh
superloopy loop review --status passed --artifact .superloopy/evidence/gate.json --notes "<summary>" --json
superloopy loop checkpoint --goal-id G001 --status complete --evidence "<summary>" --quality-gate .superloopy/evidence/gate.json --json
```

When a final proof command can be satisfied from cache but the task needs fresh evidence, capture a rerun variant in the artifact, for example Gradle `--rerun-tasks` on the focused JVM test. Use this for final evidence capture, not as a default tax on every local check.
