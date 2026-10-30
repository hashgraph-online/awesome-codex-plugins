# statechart scripts

`statechart` model-checks a TLA+ spec with TLC, learns the verdict of every rule, and writes a Markdown report plus a Mermaid state chart that shows the reachable states and the shortest path to each broken rule.

## Run it

```sh
skills/statechart/scripts/statechart SPEC.tla [--config FILE] [--view FILE] [--out DIR]
```

- `--config` defaults to `SPEC.cfg` beside the spec. A missing config stops with exit 2.
- `--view` is an ES module that labels the chart. It may export only `state(vars)`, `step(action, from, to)`, `group(vars)`, `colors`, and `title`. Colors are `blue`, `orange`, `purple`, `yellow`, `teal`, `tan`, `pink`.
- `--out` defaults to `SPEC-chart` beside the spec. The folder must not exist yet or must be empty. Output is staged in a hidden sibling folder and renamed into place only when the check finishes, so an interrupted or failed run leaves nothing behind.

The launcher is POSIX `sh`. It follows symlinks to find `statechart.mjs` and runs it with Node.js 22 or later (exit 127 if there is none). There are no npm dependencies.

## Toolchain

Set `TLA2TOOLS` to a `tla2tools.jar` and, if `java` is not on `PATH`, `JAVA` to a Java 11+ binary. Without `TLA2TOOLS`, the command downloads tla2tools 1.7.4 from the official GitHub release once, checks its pinned sha256, and keeps it in `~/.cache/endostack/statechart` (override with `STATECHART_CACHE`; set `STATECHART_NO_DOWNLOAD=1` to forbid the download). Java itself is never installed for you; the error message says how.

## Output

| File | When |
| --- | --- |
| `report.md` | always; also printed to stdout |
| `chart.mmd` | when there is a chart (up to 500 distinct states the whole graph; above that only the paths to broken rules; none if nothing broke) |
| `tlc.out` | always: TLC's output on the config as written, rendered as plain TLC prints it |
| `tlc-RULE.out` | each broken temporal property, and each broken rule whose path the chart does not show |

Exit codes: 0 every rule holds, 1 some rule breaks, 2 error (bad arguments, config refused, SANY or TLC failure, view error, output folder conflict, worker killed), 130 or 143 after SIGINT or SIGTERM.

## How a check runs

1. `lib/config.mjs` reads the config the way TLC does and refuses anything TLC would reject or might read differently.
2. SANY's XML exporter gives the variables in declaration order and each definition's level (`lib/sany.mjs`).
3. `lib/verdicts.mjs` runs TLC on the config as written; that run's exit decides the command's exit. Because TLC stops at the first violation, it reruns without each broken rule (bounded at 100,000 distinct states after the first break) until every rule has a verdict.
4. When TLC saw at most 500 states, a drawing run dumps the state graph as DOT and prints a tagged mark for every state that breaks an invariant (`lib/pipeline.mjs`, `lib/graph.mjs`).
5. A breadth-first search from the initial states finds the shortest path to each bug. The view labels states and steps, and `lib/chart.mjs` builds flat, nested, or parallel-region charts; a regions chart is drawn only if its moves equal the model's moves.
6. `lib/mermaid.mjs` and `lib/report.mjs` write the chart and report; `lib/tlc-output.mjs` renders TLC's `-tool` output as plain text.

The supervisor in `statechart.mjs` runs the check in a worker process group and starts a small janitor shell that holds a pipe from the supervisor. If the supervisor dies for any reason, including SIGKILL, the pipe closes and the janitor kills the worker group (and any TLC JVM) and removes the staging and temp folders.

## Tests

```sh
node --test skills/statechart/scripts/test/
TLA2TOOLS=/path/to/tla2tools.jar node --test skills/statechart/scripts/test/
```

Without `TLA2TOOLS` the live-TLC tests are skipped and everything else runs on recorded TLC output. `test/corpus/` holds 26 small specs (with configs and some views), each with `recordings/` (SANY XML, every TLC run's output, and the DOT dump) and `expected/` (report, chart, TLC output files, exit code). Replay tests serve the recordings in place of Java; the CLI tests do the same through the `STATECHART_REPLAY` hook. After changing the tool, re-record against a real TLC and review the diff:

```sh
TLA2TOOLS=/path/to/tla2tools.jar node skills/statechart/scripts/test/support/record.mjs [case ...]
```
