# Skill audit evidence

This skill's `scripts/audit.sh` delegates to `ao skills audit`. Its default
`skill-audit.v2` schema is [audit-report.json](../schemas/audit-report.json) and reports:

- **Conformance:** selected static package checks, their applicability, findings,
  checked scope and explicit untested scope. Canonical uses the existing source
  checker; portable checks identity, field allowlist and types; external observation
  does not enforce repository metadata or claim portable compatibility.
- **Effects:** located declared/detected reads, disclosure, credentials, network,
  execution and mutation. Every observation includes a source path, line, snippet
  and literal reachability chain. A remote response piped into a shell is surfaced
  as that concrete conditional failure path, not hidden by safety labels.
- **Behavior:** `NOT_PROVEN`, zero trials. Skill Eval and native trial owners retain
  behavioral evidence; static inspection neither launches nor fabricates trials.
- **Authoring:** located generic-advice suspicions, always non-gating. Necessary
  prohibitions, phase counts, section labels and optional files are not defects.

The scanner starts at SKILL.md and follows literal package-local Markdown links
and recognized script invocations. Referenced siblings resolve inside the declared
repository/catalog; their contents and transitive effects remain uninspected.
Dynamic paths, external commands, conditional loading, binary assets, runtime
permissions and disclosure controls remain limitations. No count, absence of
matches or inventory certifies full reachability or safety. Effect status remains
`NOT_PROVEN` even when selected static conformance is `PASS`.

Canonical source and exported portable packages are distinct subjects. Profile
selection follows package location unless `--profile` is explicit; canonical
source metadata is not portable host metadata. Host checks remain necessary;
this bounded audit does not attest installed invocation policy or host execution.

Exit 0 means only no selected static conformance failure; exit 1 means a concrete
conformance defect; exit 2 means invalid inputs or destination. `--strict` is
accepted but cannot turn suspicions into blockers. JSON defaults to stdout;
`--json PATH` creates a new protected external non-Git report without overwrite.

## Explicit legacy compatibility

`audit.sh --legacy` emits the accepted S1 report under
[audit-report-legacy.json](../schemas/audit-report-legacy.json), with the original field/exit contract.
Consumers that need the old `verdict`, `pass1`, `pass2`, `density`, `rubric`,
`craft` and `authoring` fields must opt in explicitly; do not use legacy scores
to rank or optimize packages. The shared conformance-profile/trigger CI consumer
is unchanged. In the AgentOps source checkout the option's callers are
`tests/integration/test_skill_audit.bats`,
`tests/scripts/skill-audit-rubric-pass.bats`,
`docs/reference/skill-quality-rubric.md`, `README.md` and
`docs/install-day2-ops.md`, and in this skill `skill-template.md`,
`authoring-doctrine.md`, `skill-auditor.feature` and
`schemas/audit-report.json`; `git grep -l -e --legacy` lists them (`plugin/`
copies regenerate; `CHANGELOG.md` is history). Retire it together with them.

### What the legacy report contains

`--legacy` runs the structural `heal.sh --check --strict` pass, eight content
checks, an advisory package-readiness score, a keyword density block, craft
instrumentation (`craft_score.py`) and an authoring prose scan
(`authoring_scan.py`). Check IDs, thresholds and severities come from
[skill-conformance-profiles.yaml](skill-conformance-profiles.yaml); field
meanings are in the legacy schema. These are wording heuristics: none of them
establishes semantic completeness, safety or effectiveness, and no package
should gain a section, bullet or phrase only to satisfy one. The detection
power of the two advisory scanners is mutation-tested by
`scripts/test-craft-mutations.sh` and `scripts/test-authoring-mutations.sh`.

## Calibration rule

Before tightening any audit check, run it across every canonical skill. A
proposed rule that fails valid concise skills is miscalibrated unless the
repository contract itself requires those skills to change.
