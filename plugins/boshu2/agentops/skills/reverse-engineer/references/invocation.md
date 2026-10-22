# Reverse Engineer: script invocation and maintenance

Script-level detail for Phase 1 of the reverse-engineer skill. The skill body
owns the evidence rules, verdicts and routing; this file owns flags, outputs,
compatibility, fixtures and the self-test.

## Invocation contract

Required: `product_name`. Common flags: `--mode=repo|binary|both`, `--upstream-repo`, `--upstream-ref` (requires the selected checkout to be at that exact commit and records its resolved SHA in `clone-metadata.json`), `--local-clone-dir` (selects that exact tree, including a non-Git tree; it never falls back to the caller's checkout), `--output-dir` (default `.agents/scratch/reverse-engineer/<product>/`), `--security-audit`, `--materialize-archives` (authorized-only opt-in; embedded-archive extraction is off/index-only by default), `--authorized` (mandatory for binary mode — refuses without it). Full list: `python3 skills/reverse-engineer/scripts/reverse_engineer.py --help`.

## Outputs

Phase-1 teardown under `output_dir/`: `feature-inventory.md`, `feature-registry.yaml`, `feature-catalog.md`, `spec-architecture.md`, `spec-code-map.md`, `spec-clone-vs-use.md`, `spec-clone-mvp.md`, plus `spec-cli-surface.md` only when a CLI is detected. `clone-metadata.json` is written whenever an upstream repo/ref is selected and binds the exact analyzed commit, including an already-present checkout. Security mode adds `output_dir/security/`: `threat-model.md`, `attack-surface.md`, `dataflow.md`, `crypto-review.md`, `authn-authz.md`, `findings.md`, `reproducibility.md`, `validate-security-audit.sh`. Phase-2 adds the caller-authored `steal-map.md`.

- **Artifact directory:** the exact `--output-dir`, defaulting to
  `$REPO/.agents/scratch/reverse-engineer/<product>/`.
- **Filename convention:** the fixed phase-1 and phase-2 names above; security
  files live only in the `security/` child directory.
- **Serialization/schema format:** registry is YAML, clone metadata is one JSON
  object, and inventories/specs/steal-map are nonempty Markdown files.
- **Validator:** Phase 1 runs `validate-output.sh --phase teardown`
  automatically. The complete-output command, with `$output_dir`,
  `$security_audit`, `$sbom` and `$upstream_ref_set` (each numeric flag `0|1`),
  is in the skill body. It requires the steal-map header
  `| Their capability | Our surface today | Verdict |` and at least one row whose
  verdict is `have`, `gap`, `steal`, `park` or `reject`.

## Earlier default compatibility

Existing teardowns under `.agents/research/<product>/` remain in place and
usable. The script accepts that directory when it is passed explicitly with
`--output-dir`; that flag is caller authorization to write the teardown at the
exact selected path. It does not relocate or duplicate existing artifacts. An
invocation that omits the flag writes only to the current scratch default and
never creates output under the earlier root.
Consumers must retain the exact selected `output_dir` with their evidence
references instead of rediscovering outputs by globbing one root. The owning
skill contract is the compatibility authority; no separate migration receipt
is required.

## Reproducibility and fixtures

`--upstream-ref` binds the selected checkout to one full commit: a new clone is
checked out detached at the fetched ref, while an existing checkout must already
match or the run refuses before analysis. `clone-metadata.json` records that
resolved commit. Regression test: `bash skills/reverse-engineer/scripts/repo_fixture_test.sh`. To update a fixture when contracts legitimately change, re-run with the new pinned ref, copy the contract files into `fixtures/<product>/`, and commit.

## Self-test (acceptance)

```bash
bash skills/reverse-engineer/scripts/self_test.sh
```

Must show: feature inventory and registry generated; the exact Phase-1 validator
passes; the complete validator rejects a missing and malformed steal-map and
accepts a valid caller-authored fixture; existing-checkout ref mismatch and
output symlinks fail closed; in security mode `validate-security-audit.sh`
exits 0 only after the scaffold is completed and the secret scan passes.

## Examples

**OSS CLI in repo mode, then a steal-map.** Run Phase 1 for `cc-sdd` with `--mode=repo --upstream-repo="https://github.com/gotalab/cc-sdd.git" --upstream-ref=v1.0.0`. It clones the pinned source, scans the surface, writes inventory/registry/specs, and validates the teardown. Then inspect our live surfaces, author each `have`/`gap`/`steal`/`park`/`reject` row in `steal-map.md`, and run the complete-output validator. Supply selected steals to Plan.

**Binary analysis with security audit.** Run the skill for `ao` with `--authorized --mode=binary --binary-path="$(command -v ao)" --security-audit`. It performs authorized static analysis plus the security suite under `output_dir/security/`; the secret-scan check must pass. Use the bundled demo fixture when no real binary is authorized.

## Script troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| Refuses binary analysis | Missing `--authorized` | Add `--authorized` (explicit written authorization required). |
| No `clone-metadata.json` | `--upstream-repo` not passed | Pass `--upstream-repo` (and optionally `--upstream-ref`). |
| Fixture diff fails | Upstream changed / stale golden | Re-run pinned, refresh `fixtures/`, commit. |
| Existing teardown is under `.agents/research/` | It used the earlier default | Pass that exact directory with `--output-dir`; new runs otherwise use the scratch default. |
| `spec-cli-surface.md` missing | No Node/Python/Go CLI detected | Surface is documented in `spec-code-map.md` instead. |
