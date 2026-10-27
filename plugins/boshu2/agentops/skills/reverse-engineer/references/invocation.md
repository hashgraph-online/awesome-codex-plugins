# Reverse Engineer: script invocation and maintenance

Script-level detail for Phase 1 of the reverse-engineer skill. The skill body
owns the evidence rules, verdicts and routing; this file owns flags, outputs,
tests and fixtures. `<skill-dir>` is defined in [SKILL.md](../SKILL.md).

## Invocation contract

Required: `product_name`. Common flags: `--mode=repo|binary|both`, `--upstream-repo`, `--upstream-ref` (requires the selected checkout to be at that exact commit and records its resolved SHA in `clone-metadata.json`), `--local-clone-dir` (selects that exact tree, including a non-Git tree; it never falls back to the caller's checkout; default `.tmp/<product>/` under the current directory, so keep that out of commits), `--output-dir` (default `.agents/scratch/reverse-engineer/<product>/`; an older teardown directory such as `.agents/research/<product>/` is accepted when passed explicitly, and nothing is moved), `--security-audit`, `--materialize-archives` (authorized-only opt-in; extracts under `<local-clone-dir>/extracted`; index-only by default), `--authorized` (mandatory for binary mode — refuses without it). Full list: `python3 "<skill-dir>/scripts/reverse_engineer.py" --help`.

## Outputs

Everything the run writes lands under `output_dir/`:

- **Every mode:** `feature-inventory.md`, `feature-registry.yaml`, `feature-catalog.md`, `spec-architecture.md`, `spec-code-map.md`, `docs-features.txt`, `analysis-root-path.txt` with an empty `analysis-root/`, the registry validator wrapper `validate-feature-registry.py`, and `scratch/` (fetched sitemap, binary help and strings).
- **Repo mode:** registry groups start `impl: unclassified`; `spec-artifact-surface.md`, `contracts/repo-contract.json` (CLI, env vars with file evidence, config and schema files, and `upstream_commit` for a Git checkout), `spec-cli-surface.md` when a CLI is detected, and `artifact-registry.json` when a Node CLI ships template manifests.
- **Upstream repo or ref selected:** `clone-metadata.json`, binding the exact analyzed commit, including an already-present checkout.
- **Binary mode:** `binary-analysis.md`, `binary-symbols.txt` (the first 2,000 strings), `cli-help-tree.txt`, `cli-commands.txt`, `binary-embedded-archives.md`, and `spec-cli-surface.md` from the help tree or strings; `feature-registry.yaml` is rewritten with `impl: client` groups anchored to `binary-symbols.txt`. `--mode=both` adds `comparison-report.md`.
- **`--security-audit`:** `security/` with `threat-model.md`, `attack-surface.md`, `dataflow.md`, `crypto-review.md`, `authn-authz.md`, `findings.md`, `reproducibility.md`, and copies of `validate-security-audit.sh`, `scan-secrets.sh` and `generate-sbom.sh`; `--sbom` adds `sbom.spdx.json` (or `sbom.NOOP.md`) and `dep-risk-report.md`.
- **Phase 2:** the caller-authored `steal-map.md`.

The registry is YAML, clone metadata is one JSON object, and inventories,
specs and the steal-map are nonempty Markdown files.

**Validator:** Phase 1 runs `validate-output.sh --phase teardown`
automatically. The complete-output command, with `$output_dir`,
`$security_audit`, `$sbom` and `$upstream_ref_set` (each numeric flag `0|1`),
is in the skill body. It requires the steal-map header
`| Their capability | Our surface today | Verdict |`; every row of that table
needs both cells filled, a `(code: <file:line>)`, `(docs)` or `(hosted)` tag in
the capability cell, and one of `have`, `gap`, `steal`, `park` or `reject`;
a `steal` row needs the `code` tag. In every phase it runs
`scripts/security/scan_secrets.sh` over the whole output dir.

## Tests and fixtures

- `bash "<skill-dir>/scripts/validate.sh"` needs no Go or network.
  It checks Python syntax, that the security gate refuses an unfilled
  scaffold, that the secret scan catches seeded `key = value`, JSON-key,
  Bearer, AIza and PEM private-key header cases, a repo-mode teardown of a small tree (unclassified
  registry, scratch inside the output dir), the steal-map row rules, and that
  a wrong-ref checkout and symlinked outputs are refused.
- `bash "<skill-dir>/scripts/self_test.sh"` needs Go and writes under
  the repository's `.tmp/`. It builds a demo binary with an embedded archive,
  runs binary mode and the security audit, pins an upstream ref, and checks the
  output-path defaults and generated-tree hygiene.
- `bash "<skill-dir>/scripts/repo_fixture_test.sh"` needs network. It
  tears down cc-sdd at `v2.1.0` and compares the contracts with
  `fixtures/cc-sdd-v2.1.0/`. When contracts legitimately change, re-run with
  `UPDATE_FIXTURES=1`, review the diff, and commit.

`--upstream-ref` binds the selected checkout to one full commit: a new clone is
checked out detached at the fetched ref, while an existing checkout must already
match or the run refuses before analysis.

## Examples

**OSS CLI in repo mode, then a steal-map.** Run Phase 1 for `cc-sdd` with `--mode=repo --upstream-repo="https://github.com/gotalab/cc-sdd.git" --upstream-ref=v2.1.0`. It clones the pinned source, scans the surface, writes inventory/registry/specs, and validates the teardown. Then read the code the teardown points to, inspect our live surfaces, author each `have`/`gap`/`steal`/`park`/`reject` row in `steal-map.md`, and run the complete-output validator. Supply one-way-door steals to Plan.

**Binary analysis with security audit.** Run the skill for `ao` with `--authorized --mode=binary --binary-path="$(command -v ao)" --security-audit`. It performs authorized static analysis plus the security suite under `output_dir/security/`; the secret scan must pass. Without an authorized binary, `self_test.sh` builds a demo one (needs Go).

## Script troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| Refuses binary analysis | Missing `--authorized` | Add `--authorized` (explicit written authorization required). |
| No `clone-metadata.json` | `--upstream-repo` not passed | Pass `--upstream-repo` (and optionally `--upstream-ref`). |
| Secret scan fails the teardown | A secret-shaped value in an output file (often `binary-symbols.txt` or `scratch/`) | Open each printed `file:line`, redact the value or delete the scratch file, then re-run `validate-output.sh --phase teardown`. |
| Fixture diff fails | Upstream changed / stale golden | Re-run pinned with `UPDATE_FIXTURES=1`, review, commit. |
| `spec-cli-surface.md` missing | No Node/Python/Go CLI detected | Surface is documented in `spec-code-map.md` instead. |
