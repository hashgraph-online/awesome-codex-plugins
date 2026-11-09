# Gates Catalog

How Setup proposes quality gates from a project's stack, and how Quality surveys existing debt
with the same stacks. **Detection only ever proposes — the user decides**:
accept, edit (any shell command is a valid gate), or decline (no gates is a first-class answer;
the shift runs without automated checks). Explicit user config always beats detection.

List the stacks with `ns catalog-index --catalog gates` and read only the ones whose Detect
matches. The index prints them in match order: `Match: stack` (the default), then `Match: plugin`
(only when no stack matched), then `Match: fallback` (last). An owner's stack of the same key
replaces the shipped one, and the index names the source that won and the sources it replaced.

Two tiers, cheapest first:

- **item gate** — runs ONCE per item, right before its commit or artifact receipt; must be green to tick. Fast.
- **site inspection** — the heavier batch at an interval (every N items or every H hours); coverage,
  dead-code, Sonar.

## Site-inspection interval

Chosen at setup — every **N items** or every **H hours** (default: hourly). The inspection includes:

- **coverage as a tripwire, never a target** — no padding tests to move a number; an exclusion needs
  a written reason;
- **dead-code sweeps** (per the stack that matched);
- **Sonar-ready** (below).

## Sonar-ready

If `sonar-project.properties` exists AND a local or community SonarQube answers on its configured
host, run the batch scan at each site inspection and fix to **zero new issues** before resuming
items. Sonar is too slow to be an item gate — it is an inspection, never per-item (the proven
hourly-batch pattern). Coverage there is a tripwire (a gate on new code), never padded.

## Notes

- Zero-config holds: nothing detected → nothing proposed, and declining the proposal lands in the
  same place. Gates are opt-in, never a requirement.
- Quality runs the item-gate commands from the detected stack in report-only mode to survey existing debt,
  then proposes punch-list items the owner may accept, edit, or decline.
- The `## Gates` block lives in `punch-list.md` and stays owner-editable between and during shifts;
  hooks and the skill re-read it, so an edit takes effect from the next item. Only the agent is
  barred from editing it.

## Adding a stack

A stack is markdown, not code. One new file, and the index lists it. Do not add a stack whose
commands this shift cannot run.

```text
skills/nightshift/references/compose/gates/<key>.md
```

Copy `skills/nightshift/references/templates/gates-stack.md`. The file name is the key. The H1 is
`# <Stack> — <the signal that detects it>`. The body is Detect, Item gate, Site inspection, and
Notes, in that order. Detect carries one `Match:` line: `stack`, `plugin`, or `fallback`.

An owner adds a stack without a pull request: in this project's `.nightshift/catalogs/gates/`,
in the user folder for every project (`$XDG_CONFIG_HOME/nightshift/catalogs/gates` on POSIX,
`%APPDATA%\nightshift\catalogs\gates` on Windows), or in a folder named by
`catalogs.gates.paths`. `ns catalog-new --catalog gates --key <key>` starts one from the
template in force, `catalogs.gates.template` names the owner's own template, and
`ns catalog-index --catalog gates --check-draft FILE` checks what Nightshift reads from a draft.
[Owner knobs](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/knobs.md#catalogs) lists the precedence.
Every catalog works the same way: [Add to a catalog](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/add-to-a-catalog.md).
