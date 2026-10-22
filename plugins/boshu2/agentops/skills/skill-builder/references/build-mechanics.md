# Build and check mechanics

Detail for `scripts/build.sh`, `scripts/heal.sh` and recovery from partial
creation. The audit report, its exit codes and the legacy audit schema are in
[audit checks](audit-checks.md).

## Creation inputs and reports

Supply one input to `scripts/build.sh`: `from-scratch`, `from-template` or
`absorb-external <slug> --from <path>`. The caller can supply `SKILL_TIER`,
`SKILL_DEPENDENCIES`, `SKILL_CAPABILITIES` and `SKILL_EFFECTS`; lists are JSON
arrays. An inline answer needs no output file.

The shell entrypoints delegate creation and source checks to `ao skills build`
and `ao skills check-source`. Development checkouts run their Go source;
installed packages need an `ao` built from this version. Tests can set
`AO_SKILL_BUILDER_BIN` to an explicit binary. Build JSON goes to stdout. To save
it, pass `--report /absolute/external/directory/build.json` in an existing
protected non-Git directory. Existing report paths are never replaced.

The [build-report schema](../schemas/build-report.json) retains its old fields,
permits a one-file source list, and adds `authoring_state: scaffold` and
`semantics_evaluated: false`. `structure_check_pass` describes mechanical
creation/projection only, even when true. There is no default workspace report;
consumers of the former `.agents/scratch/skill-builder/` path must select a
report destination or read stdout.

## Exit codes

| Command | Exit 0 | Exit 1 | Exit 2 |
|---|---|---|---|
| `build.sh` | Created; always reports scaffold state | Invalid creation input, including an invalid slug or missing template/external input, or an existing destination | Wrapper syntax error |
| `heal.sh` | No finding, or findings in non-strict check mode | Findings under `--strict` or `--fix` | Invalid target, or `ao` could not run |

Exit 0 never means the skill is safe or effective.

## Staged creation and recovery

Creation is staged, not atomic across source, catalogs, projections and reports.
If a later stage fails, retain the created source and any report, capture the
command's exit and diagnostic, and inspect which outputs exist. Report source
creation separately from projection/check completion. `structure_check_pass:
false` does not mean no files were created; a report-write failure can also
leave source behind. Never call that partial result a completed package or
remove it just to rerun creation. An existing target is deliberately rejected.

Recover from the observed stage within existing authority: repair the named
obstruction, finish authoring the retained source if it is still a scaffold,
then run the strict source check, owning projection commands and audit. Retain
the failed report as evidence and use a new authorized report path if one is
needed. Verify the retained source and final generated output; report remaining
failures instead of resetting completion history.

## Check and heal targets

Check/heal targets must be real direct children of `skills/`; reject missing
paths, traversal and symlink spellings. Check mode is read-only. Fix mode
regenerates owned projections for explicit targets and does not invent source
behavior. Findings name their code, target and concrete issue. Checks cover the
slug/name match, description, API version, metadata, live dependencies and
linked resources.

`scripts/regen-all.sh` is the integrated projection recipe;
`scripts/generate-skill-mesh.py` is the existing scoped surface. Do not repeat
work already performed by `build.sh` unless source changes require it.
