# Render And Verify

Use this rule file before the first render and before delivery. It owns the render command, the report, the repair loop, and the closing report.

## 1. Command

```bash
bash <skill-dir>/scripts/render-diagram.sh --spec <out-dir>/<slug>.diagram.json --out-dir <out-dir> \
  [--formats html,jpg[,pdf]] [--theme light|dark] [--scale 1-4] [--name <slug>]
```

- `<skill-dir>` is this skill's own folder, written as an absolute path or a path from the working directory.
- Defaults: `--formats html,jpg`, `--scale 2`, theme from the spec (`light` when absent).
- `--browser <path>` or `HYPER_DIAGRAM_BROWSER` picks a browser; `--list-browsers` shows what was found.
- Graph types (`architecture`, `flowchart`, `dataflow`, `state`, `class`, `erd`) need elkjs. The script downloads it once and checks its SHA-256; `HYPER_DIAGRAM_ELK` points to an already verified copy for offline machines.

## 2. Exit Codes And Report

| Exit | Meaning | Next step |
|---|---|---|
| 0 | `status: pass`; outputs written | View the JPG (§4) |
| 1 | `status: fail`; files written for inspection only | Repair (§3) |
| 2 | Usage or spec error (`SPEC_INVALID`, `BAD_FORMAT`, ...) | Fix the command or the JSON |
| 3 | Blocked (`BROWSER_MISSING`, `ELK_UNAVAILABLE`, `RUNTIME_NO_RESULT`) | Report the blocker and the unblocking step; keep the spec |

The report on stdout carries `status`, `type`, `canvas`, `counts`, `outputs`, `pdfPages`, `errors`, and `warnings`.

## 3. Repair

| Code | Meaning | Usual fix |
|---|---|---|
| `TITLE_MISSING`, `DESCRIPTION_MISSING` | required text absent | write it |
| `BAD_ID`, `DUPLICATE_ID`, `UNKNOWN_ENDPOINT`, `UNKNOWN_GROUP`, `UNKNOWN_PARENT` | broken references | fix the ids |
| `TYPE_UNKNOWN`, `NO_NODES`, `BAD_DATE`, `TASK_LENGTH`, `NOTE_TARGET` | spec shape | follow `references/spec-format.md` |
| `TEXT_OVERFLOW`, `NODE_OVERLAP`, `LABEL_OVERLAP`, `LABEL_OVERLAPS_NODE` | crowding | shorten text, move detail into `sub`, raise `spacing` |
| `NODE_CROSSES_GROUP`, `GROUP_OVERLAP` | group membership | set `group` on the node or `parent` on the group |
| `EDGE_CROSSES_NODE` | a route runs through a box | reorder nodes, change `direction`, or regroup |
| `PDF_MULTIPAGE`, `JPG_FAILED`, `PDF_FAILED`, `SCRIPT_LEFT` | export | re-run; report if it repeats |
| warning `EDGE_CROSSINGS` | edges cross | reorder nodes in the spec; ELK keeps model order |
| warning `DENSE_DIAGRAM`, `WIDE_DIAGRAM` | too big | split (`rules/diagram-selection.md` §2) or set `direction` |

- At most three repair passes after the first render. Revert a pass that adds errors.
- Fix meaning before looks: never drop an element or a relation only to pass a check without saying so.

## 4. Visual Check

The checks cannot see meaning. Open the JPG and confirm:

- the main path reads in one direction without zig-zag;
- no label sits on the wrong edge or far from its edge;
- the grouping says what the material says;
- nothing important is tiny or cut.

## 5. Closing Report

Report in Korean: the output paths (spec, HTML, JPG, PDF), the type and why, a two-line structure summary, the elements marked inferred, remaining warnings, and the verification that ran (exit code, pages, visual check).

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Headless Chromium `--dump-dom`, `--screenshot`, `--print-to-pdf`, and the one-page condition | `.hyper/research/21.diagram-skill.md` execution checks, 2026-11-08 |
| ELK layered layout keeps model order when asked | <https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html> |
| The code set, exit codes, and the three-pass cap | this package's `scripts/render-diagram.sh` and `assets/runtime/run.js` |

### Evidence grade

`LOCAL` - the codes and the repair table describe this package's own runtime.
