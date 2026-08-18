---
name: contam-mcp
description: Use when working with CONTAM projects through the local contam MCP server, including discovering CONTAM executables and API integrations, listing .prj/.sim/.wth/.ctm files, inspecting or diagnosing project references, cloning scenario folders, running baseline/intervention case matrices, using contamxpy for step-by-step co-simulation, updating weather or contaminant references, running simulations, upgrading projects, comparing .sim results, analyzing text outputs, exporting simulation text, or using bridge sessions for zone/path/AHS metadata and adjustments.
---

# CONTAM Plugin

Use this skill when the user wants to inspect, diagnose, clone, batch-run, co-simulate, upgrade, compare, analyze, or export CONTAM projects through the `contam` MCP server.

## Setup

- The plugin starts the MCP server through `scripts/start-contam-mcp.ps1`.
- The plugin also ships `scripts/Invoke-ContamProjectGuard.ps1` for local PRJ hygiene, input checks, output cleanup, result-profile updates, and XLog triage.
- The current official CONTAM release checked for this workflow is CONTAM 3.4.0.8, with command-line tools such as ContamX 3.4.0.3. Re-check the official NIST release page before changing executable assumptions.
- `CONTAM_PLUGIN_ROOT` is set by the launcher when the plugin runs from this repository.
- `CONTAM_HOME` may point to the directory containing CONTAM executables.
- `CONTAM_CHINESE_HOME` may point to an extracted `contam_chinese` release; when set, the launcher uses those localized executables unless explicit tool paths override them.
- Optional executable overrides: `CONTAMX_PATH`, `CONTAMW_PATH`, `PRJUP_PATH`, `SIMREAD_PATH`, `SIMCOMP_PATH`.
- The server targets command-line tools such as `contamx3.exe`, `prjup.exe`, `simread.exe`, and `simcomp.exe`; do not assume GUI automation through `contamw3.exe`.

## Standard Flow

1. Confirm the installation before running a case:
   - `discover_contam_installation`
   - `discover_contam_api_stack`
2. Find candidate project and result files:
   - `list_contam_case_files`
3. Inspect the project before edits or simulation:
   - `inspect_contam_project`
   - `diagnose_contam_project`
4. If references are wrong, update only the requested fields:
   - `update_contam_project_references`
5. For baseline/intervention studies, clone scenarios before running:
   - `create_contam_case_variant`
   - `run_contam_case_matrix`
6. When a PRJ can run but needs ContamW-visible layout, apply SketchPad data before GUI review:
   - `apply_contam_sketchpad_layout`
7. Before asking the user to open or run in ContamW, use the project guard script for local checks:
   - `scripts/Invoke-ContamProjectGuard.ps1 -ProjectPath <file.prj> -Mode InputCheck -ResultProfile GuiSafeResults -CleanOutputs -RequireSingleProject`
8. For paper-style API workflows, use `contamxpy` when available:
   - `inspect_contamxpy_project`
   - `run_contamxpy_cosimulation`
9. Run or upgrade the project:
   - `run_contam_simulation`
   - `upgrade_contam_project`
10. Compare, export, or quickly triage results:
   - `compare_contam_sim_results`
   - `export_contam_sim_text`
   - `analyze_contam_text_results`

## Project Guard Flow

Use `Invoke-ContamProjectGuard.ps1` whenever a generated or modified PRJ is expected to open in ContamW or be handed to another user.

Typical commands:

```powershell
.\scripts\Invoke-ContamProjectGuard.ps1 `
  -ProjectPath "<case>\model.prj" `
  -Mode InputCheck `
  -ResultProfile GuiSafeResults `
  -CleanOutputs `
  -RequireSingleProject
```

For a command-line full run:

```powershell
.\scripts\Invoke-ContamProjectGuard.ps1 `
  -ProjectPath "<case>\model.prj" `
  -Mode Run `
  -ResultProfile GuiSafeResults
```

Use this flow before GUI work:

1. Keep case-specific data outside the plugin, for example `case-spec.json`, `layout.json`, `inputs/*.csv`, and `ERRORS.md` in the case folder.
2. Avoid local absolute paths in shared PRJ files; prefer relative case-local references so another user can move the case folder.
3. Keep only one active `.prj` in a case folder unless the user explicitly wants scenarios; remove failed variants and stale result files.
4. Repair UTF-8 BOM if present. CONTAM expects the format line at byte 0; PowerShell writes can accidentally break this.
5. Run `InputCheck` after every PRJ edit. A ContamX input check passing means the text structure is readable; it does not prove SketchPad geometry is GUI-valid.
6. Run full simulation from command line to separate solver failures from ContamW GUI result handoff failures.
7. Inspect the newest `.xlog`; trust `Simulation completed successfully.` over a GUI impression that the console "closed".
8. If a manual ContamW run reports `CONTAMX.EXE: simulation terminated abnormally` but command-line ContamX exits 0 and writes a successful XLog, treat it as a GUI result handoff/loading issue, not a solver issue.

For generated models that are meant to match a hand-built ContamW reference, pass structural expectations into the guard:

```powershell
.\scripts\Invoke-ContamProjectGuard.ps1 `
  -ProjectPath "<case>\model.prj" `
  -Mode InputCheck `
  -ExpectedZoneCount 9 `
  -ExpectedPathCount 49 `
  -ExpectedAmbientPathCount 40 `
  -ExpectedInterzonePathCount 9 `
  -MinimumAmbientPathsPerZone 1
```

Use the expected counts from the reference case, not from the generated model. A model can pass ContamX input checks while still being too simplified for the user's intended ContamW case.

## Reference PRJ Learning Flow

When the user provides a hand-built ContamW `.prj` as a reference for a generated project, treat the hand-built file as the structural source of truth before changing generation logic.

1. Compare section counts first: zones, source/sink elements, flow elements, flow paths, source/sinks, schedules, and wind pressure profiles.
2. Compare flow path inventory by class: zone-to-ambient paths, interzone paths, vertical or stair paths, and paths with wind pressure profile fields enabled.
3. Preserve every real opening represented in the reference model. Do not collapse multiple facade leaks, doors, windows, supplies, and exhausts into one generic ambient path per room unless the user explicitly asks for a simplified model.
4. Preserve inter-floor/stair connectivity as explicit paths. If the reference uses a stair or vertical connection, do not replace it with same-floor hall links just to make the SketchPad layout easier.
5. If the reference has no wind pressure profiles and uses neutral exterior path fields, do not introduce WPC profiles merely because they look more physical. Add WPC only when the case definition, weather study, or user request requires it.
6. Renaming zones, flow elements, schedules, and sources is useful for readability, but after renaming verify that source/sink rows, initial concentrations, schedule ids, and zone ids still point to the same physical rooms.
7. For GUI-facing cases, prefer a complete path inventory plus simpler, valid SketchPad geometry over a visually clean drawing that hides or omits airflow paths.

Recent lesson from a two-floor SF6/COMIS-style comparison: the hand-built reference had 9 zones, 18 flow elements, and 49 flow paths (40 ambient and 9 interzone), while a generated GUI variant had 9 zones, 20 flow elements, and 27 flow paths (20 ambient and 7 interzone). The useful correction is not to copy the case values into the plugin, but to force generated workflows to carry over the reference model's path inventory and check ambient/interzone counts explicitly.

## Case Matrix Flow

Use `run_contam_case_matrix` when the user needs a complete case workflow from an existing `.prj`:

1. Keep the original project as the baseline source.
2. Create one named folder per scenario.
3. Apply only supported `.prj` reference changes when requested: `weatherFile`, `contaminantFile`, `continuousValuesFile`, `discreteValuesFile`, `wpcFile`, `ewcFile`.
4. Run `testInputOnly` first for new or uncertain cases.
5. Run full simulations after references and input checks pass.
6. Use `analyze_contam_text_results` for quick `.xlog` or `simread` text triage, then write separate post-processing scripts for final charts or paper tables when needed.

## SketchPad Layout Flow

Use `apply_contam_sketchpad_layout` when an existing `.prj` already has simulation records but needs a ContamW-visible drawing.

1. Inspect the project first to confirm zones, paths, source/sinks, and levels exist.
2. Convert the user's verbal description, hand sketch, paper plan, or screenshot into a small layout spec.
3. Use rectangles for simple rooms, clockwise orthogonal `polygon` points for jogged rooms, and explicit `wallSegments` for shared partitions that are visible in the sketch.
4. Let the tool generate wall corner/tee/cross icons, zone icons, source/sink icons, and SketchPad size/scale metadata.
5. Put all essential real doors, windows, supply/exhaust openings, and sources in explicit `pathIcons` or `sourceSinkIcons`. If a path is hidden and the user saves/runs from ContamW, ContamW may rewrite the PRJ from SketchPad state and drop that path.
6. Put each airflow path icon on the wall that matches its PRJ direction field. A wrong side commonly produces Building Check messages such as `The same zone is on both sides of the wall that the path is on.`
7. Avoid crowded or ambiguous tee/cross wall nodes. If ContamW draws long unintended wall lines or reports undefined zones, replace the layout with simpler closed room rectangles and valid shared-wall door icons.
8. Be cautious with wall icon type `20` in generated layouts. It can be valid in official projects, but in some generated wall graphs it triggered ContamW GUI crashes; prefer simpler wall graphs or side-specific stable nodes and verify manually.
9. For GUI review or screenshots, set `cleanDisplay: true` so pseudo-geometry is hidden and unplaced/helper paths are omitted. Use `hideAirflowPathIcons: true` only for a read-only screenshot pass, not for a model that the user will save or run from ContamW.
10. Prefer writing to `outputPath` for a first pass.
11. Run the project guard `InputCheck` after layout changes, then ask the user to manually open in ContamW for Building Check screenshots if needed.

Treat this as template-based SketchPad generation, not proof that ContamW will exactly reproduce a paper figure. Complex floor-plan tracing, curved geometry, and publication-style airflow diagrams still need dedicated post-processing or manual GUI checks.

## ContamW Building Check Playbook

When the user reports ContamW Building Check messages:

- `At least one zone is not defined on level`: the SketchPad walls usually do not form closed regions on that level. Simplify to closed rectangles or fix wall graph nodes.
- `The same zone is on both sides of the wall that the path is on`: the path icon is on the wrong wall side, lies inside a zone, or the surrounding wall does not divide two zones. Move the icon to the correct shared/exterior wall and align its direction.
- `Zone not connected to ambient by variable flow link`: ambient links may exist in PRJ records but are hidden or not recognized in SketchPad. Show one valid exterior variable flow path per relevant zone.
- `Vertical path is not above a sublevel` or floor same-zone errors: do not fake stairs with arbitrary vertical path icons. Either model a proper sublevel/stair representation or keep the uncertain vertical connection out of the GUI-run PRJ and document the assumption.
- `PathList reordering error` or repeated possible level errors: stop editing the GUI variant, restore from the data spec or a known-good PRJ, then reapply a simpler layout.

Always record the user-visible message and the fix in a case-local `ERRORS.md` or equivalent notes file. Do not commit case-local logs or generated outputs into the plugin repository.

## Result Output Profiles

Prefer the guard's `GuiSafeResults` profile when the user will run from ContamW:

```text
doDlg=1 pfsave=1 zfsave=1 zcsave=0
ach=1
csm=1 srf=1 log=1
```

This follows a known working output pattern and avoids `zcsave=1`, which can trigger ContamW result handoff/display problems in generated models.

Use `NoResults` only for GUI crash isolation. If `NoResults` runs but result display fails, run the same PRJ with command-line ContamX and parse XLog/results outside the GUI.

Do not treat a ContamX console window closing after Enter as a failure by itself. Check the newest `.xlog`; if it says `Simulation completed successfully.`, the run completed normally.

## Paper/Report Workflow

For literature reproduction or report cases, keep the plugin generic and keep all paper-specific values in case-local files. A report generally needs:

- zone table: names, levels, areas, volumes, temperatures, initial concentrations
- airflow elements: leakage area/model/exponent and source table references
- airflow paths: zone-to-zone and zone-to-ambient connectivity
- species/source/schedule settings
- weather/run-control settings
- ACH and contaminant time-series outputs
- comparison and assumptions

The ContamW SketchPad screenshot is optional unless explicitly requested. It is a model-check artifact, not the primary evidence.

## Bridge Sessions

Use bridge sessions when the user needs zone, path, ambient target, AHS, or contaminant metadata, or when they need controlled changes during a run:

- `start_contam_bridge_session`
- `get_contam_bridge_session`
- `list_contam_bridge_entities`
- `advance_contam_bridge_session`
- `close_contam_bridge_session`

Always close sessions when finished. For ambiguous path or zone selections, list entities first and use stable ids or selector labels rather than guessing.

## Paper API Flow

Use `discover_contam_api_stack` when the user references the CONTAM API paper, `contamx-lib`, `contamxpy`, `contamp-lib`, ANT, Rhino, or Grasshopper.

- If `contamxpy` is available, prefer `inspect_contamxpy_project` for API-level metadata and `run_contamxpy_cosimulation` for time-step control, custom control logic, zone concentration sampling, flow sampling, and supported dynamic adjustments.
- If ANT is unavailable, explain that Rhino/Grasshopper + ANT are needed for the paper's 3D/model-creation path.
- Do not claim full `contamp-lib` project creation unless Rhino/Grasshopper ANT or a callable ContamP/contamp-lib binding is actually present.

## Safety

- Prefer read-only inspection before modifying `.prj` files.
- Before changing references, report the field names being changed and keep the edit scoped to the requested weather, contaminant, WPC, EWC, or library references.
- Write outputs outside the plugin repository.
- Treat scenario generation as template-based cloning, not full `contamp-lib`-style geometry/model creation.
- Treat `contamxpy` as optional; if missing, run the repository setup script or ask the user before installing into a persistent environment.
- If an executable cannot be found, ask the user to set `CONTAM_HOME` or the specific executable override instead of searching personal directories.
