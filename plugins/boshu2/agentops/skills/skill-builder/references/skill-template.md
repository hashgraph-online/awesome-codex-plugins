# Skill source authoring contract

Choose the smallest shape that communicates the actual behavior. No heading,
helper, reference directory, role, output file or scoring target is mandatory.
Canonical source uses AgentOps host metadata, which every runtime loads
directly. See [Codex parity](codex-parity.md).

A completed skill must make these meanings unambiguous, in prose or examples:

- applicability and required inputs;
- authority and possible effects;
- the operation and its inline result or necessary artifact;
- how completion is established;
- what happens with missing inputs, failed operations or unavailable authority.

For example, a read-only adapter can say in one paragraph: “For a request to
inspect the current branch, run `git status --short` in the caller-selected
repository. Report the changed paths inline. Do not alter files or Git state.
Finish after the command succeeds and the paths are reported; if the directory
is not a repository or Git fails, report that error and stop.” This needs no
validator script or output-file section.

The initializer creates `SKILL.md` with metadata defaults, placeholders and
`metadata.authoring_state: scaffold`. Complete the behavior and remove that
state before strict source checking. Deleting a marker cannot prove the prose
complete: fresh semantic review is still necessary.

`heal.sh --check --strict skills/<slug>` checks identity, source fields,
explicit scaffold state and required linked resources without mutating;
`heal.sh --fix skills/<slug>` projects only structurally valid explicit targets
and invents no behavior. What `audit.sh` and its `--legacy` option report, and
how the shared [profile](skill-conformance-profiles.yaml) sets severities, is in
[audit checks](audit-checks.md). No static PASS/WARN/FAIL establishes semantic
completion, safety or effectiveness.

The package-readiness and craft scores are legacy advisory compatibility data.
Do not add content to raise them. To decide which prose earns a place, use the
admission test in [changing existing text](authoring-doctrine.md#change-existing-text-at-its-owning-layer).
