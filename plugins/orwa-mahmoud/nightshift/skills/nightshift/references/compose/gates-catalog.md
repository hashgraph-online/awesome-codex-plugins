# Gates Catalog

How Setup proposes quality gates from a project's stack, and how Quality surveys existing debt
with the same table. **Detection only ever proposes — the user decides**:
accept, edit (any shell command is a valid gate), or decline (no gates is a first-class answer;
the shift runs without automated checks). Explicit user config always beats detection.

Two tiers, cheapest first:

- **item gate** — runs ONCE per item, right before its commit or artifact receipt; must be green to tick. Fast.
- **site inspection** — the heavier batch at an interval (every N items or every H hours); coverage,
  dead-code, Sonar.

## Detection table (first match wins; monorepo-aware — detect per top-level package dir)

| Signal | Item gate (every item, fast) | Site inspection (interval, heavy) |
|---|---|---|
| `package.json` + `tsconfig.json` | `eslint` + `tsc --noEmit` + unit tests | coverage delta, `knip`/`ts-prune` dead-code sweep |
| `pyproject.toml` / `requirements.txt` | `ruff` + `mypy` + `pytest` | coverage, `vulture` dead-code sweep |
| `go.mod` | `go vet` + `go test ./...` | `go test -race`, coverage |
| `Cargo.toml` | `cargo clippy` + `cargo test` | coverage (`tarpaulin`) |
| `Chart.yaml` / kustomize | `helm template \| kubeconform` (changed charts) | full catalog render |
| `.claude-plugin/` or `.codex-plugin/` at the work-target root **or** `plugins/<name>/` | `bats -r tests/` when tests exist; tracked `*.sh` through `shellcheck -x`; `claude plugin validate . --strict` | repeat the item gate |
| `Makefile` (fallback) | `make lint test` if those targets exist | — |
| nothing detected | — | — |

## Site-inspection interval

Chosen at setup — every **N items** or every **H hours** (default: hourly). The inspection includes:

- **coverage as a tripwire, never a target** — no padding tests to move a number; an exclusion needs
  a written reason;
- **dead-code sweeps** (per the table);
- **Sonar-ready** (below).

## Sonar-ready

If `sonar-project.properties` exists AND a local or community SonarQube answers on its configured
host, run the batch scan at each site inspection and fix to **zero new issues** before resuming
items. Sonar is too slow to be an item gate — it is an inspection, never per-item (the proven
hourly-batch pattern). Coverage there is a tripwire (a gate on new code), never padded.

## Notes

- Zero-config holds: nothing detected → nothing proposed, and declining the proposal lands in the
  same place. Gates are opt-in, never a requirement.
- Quality runs the item-gate commands from this table in report-only mode to survey existing debt,
  then proposes punch-list items the owner may accept, edit, or decline.
- The `## Gates` block lives in `punch-list.md` and stays owner-editable between and during shifts;
  hooks and the skill re-read it, so an edit takes effect from the next item. Only the agent is
  barred from editing it.
