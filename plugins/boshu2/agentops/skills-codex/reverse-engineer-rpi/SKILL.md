---
name: reverse-engineer-rpi
description: "Run reverse engineer RPI."
---
# $reverse-engineer-rpi

Reverse-engineer a product into a mechanically verifiable feature inventory + registry + spec set, with optional security-audit artifacts and validation gates.

## Hard Guardrails (MANDATORY)

- Only operate on code/binaries you own or have **explicit written authorization** to analyze.
- Do not provide steps to bypass protections/ToS or to extract proprietary source code/system prompts from third-party products.
- Do not output reconstructed proprietary source or embedded prompts from binaries (index only; redact in reports).
- Redact secrets/tokens/keys if encountered; run the secret-scan gate over outputs.
- Always separate: **docs say** vs **code proves** vs **hosted/control-plane**.

## One-Command Example

```bash
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py ao \
  --authorized \
  --mode=binary \
  --binary-path="$(command -v ao)" \
  --output-dir=".agents/research/ao/"
```

If you do not have explicit written authorization to analyze that binary, do not run the above. Use the included demo fixture instead (see Self-Test below).

Repo-only example (no binary required):

```bash
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py cc-sdd \
  --mode=repo \
  --upstream-repo="https://github.com/gotalab/cc-sdd.git" \
  --output-dir=".agents/research/cc-sdd/"
```

Pinned clone (reproducible):

```bash
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py cc-sdd \
  --mode=repo \
  --upstream-repo="https://github.com/gotalab/cc-sdd.git" \
  --upstream-ref=v1.0.0 \
  --output-dir=".agents/research/cc-sdd/"
```

## Invocation Contract

Required:
- `product_name`

Optional:
- `--docs-sitemap-url` (recommended when available; supports `https://...` and `file:///...`)
- `--docs-features-prefix` (default: `auto`; detects best local docs prefix, falls back to `docs/features/`)
- `--upstream-repo` (optional)
- `--upstream-ref` (pin clone to a specific commit, tag, or branch; records resolved SHA in `clone-metadata.json`)
- `--local-clone-dir` (default: `.tmp/<product_name>`)
- `--output-dir` (default: `.agents/research/<product_name>/`)
- `--mode` (default: `repo`; allowed: `repo|binary|both`)
- `--binary-path` (required if `--mode` includes `binary`)
- `--no-materialize-archives` (authorized-only; binary mode extracts embedded ZIPs by default; this disables extraction and keeps index-only)

Security audit flags (optional):
- `--security-audit` (enables security artifacts + gates)
- `--sbom` (generate SBOM + dependency risk report where possible; may no-op with a note)
- `--fuzz` (only if a safe harness exists; timeboxed)

Mandatory guardrail flag:
- `--authorized` (required for binary mode; refuses to run binary analysis without it)

## Upstream Ref Pinning (`--upstream-ref`)

Use `--upstream-ref` to pin a repo-mode clone to a specific commit, tag, or branch. This makes analysis reproducible and allows golden fixtures to be diffed against a known baseline.

```bash
# Pin to a tag (reproducible)
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py cc-sdd \
  --mode=repo \
  --upstream-repo="https://github.com/gotalab/cc-sdd.git" \
  --upstream-ref=v1.0.0 \
  --output-dir=".agents/research/cc-sdd/"

# Pin to a specific commit SHA
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py cc-sdd \
  --mode=repo \
  --upstream-repo="https://github.com/gotalab/cc-sdd.git" \
  --upstream-ref=abc1234 \
  --output-dir=".agents/research/cc-sdd/"
```

When `--upstream-ref` is provided:

- The clone is fetched with `git fetch --depth=1 origin <ref>` and checked out to `FETCH_HEAD`.
- The resolved commit SHA is recorded in `output_dir/clone-metadata.json` for traceability.
- Without `--upstream-ref`, a `--depth=1` shallow clone of the default branch HEAD is used instead.

`clone-metadata.json` schema:

```json
{
  "upstream_repo": "https://github.com/gotalab/cc-sdd.git",
  "upstream_ref": "v1.0.0",
  "resolved_commit": "<full SHA>",
  "clone_date": "YYYY-MM-DD"
}
```

## Contract Outputs (`output_dir/`)

Repo-mode analysis writes machine-checkable contract files under `output_dir/`. These files use only relative paths, sorted lists, and stable keys — no absolute paths, no run-specific timestamps — so they can be committed as golden fixtures and diffed across runs.

**Primary contract files:**

| File | Description |
|------|-------------|
| `feature-registry.yaml` | Structured feature inventory with mechanically-extracted CLI, config/env, and artifact surface |
| `cli-surface-contracts.txt` | CLI surface: commands, flags, help text, framework, language |
| `docs-features.txt` | Features extracted from documentation (docs say vs code proves) |
| `clone-metadata.json` | Upstream repo URL, pinned ref, resolved commit SHA, clone date |

Example `feature-registry.yaml` structure:

```yaml
schema_version: 1
product_name: cc-sdd
upstream_commit: "abc1234..."
features:
  - name: cli-entry
    cli:
      language: node
      bin:
        cc-sdd: dist/cli.js
      help_text: "Usage: cc-sdd [options] ..."
  - name: config-surface
    config_env:
      config_file: ".cc-sdd/config.json"
      env_vars:
        - name: CC_SDD_TOKEN
          evidence: ["src/config.ts"]
```

> Note: Contract outputs are written by `--mode=repo` (or `--mode=both`). Binary-mode outputs (`binary-analysis.md`, `binary-symbols.txt`, etc.) remain directly under `output_dir/`.

## Fixture Test Workflow

Golden fixtures allow regression detection: commit a known-good fixture snapshot (contract files alongside the pinned `clone-metadata.json`), then diff future runs against it.

### Running Fixture Tests

```bash
bash skills/reverse-engineer-rpi/scripts/repo_fixture_test.sh
```

This script (implemented in ag-w77.3):

1. Reads `skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/clone-metadata.json` to determine the pinned upstream ref.
2. Runs `reverse_engineer_rpi.py` in repo mode with that ref into a temp output dir.
3. Diffs the generated outputs against the committed golden fixtures (`feature-registry.yaml`, `cli-surface-contracts.txt`, `docs-features.txt`).
4. Exits 0 if they match; exits non-zero with a unified diff if they drift.

The test requires network access to clone the upstream repo.

### Updating Fixtures

When contracts legitimately change (new flags, new env vars, schema bumps), update the golden fixtures:

```bash
# 1. Re-run with the pinned ref to generate fresh contracts
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py cc-sdd \
  --mode=repo \
  --upstream-repo="https://github.com/gotalab/cc-sdd.git" \
  --upstream-ref=<new-tag-or-sha> \
  --output-dir=".tmp/cc-sdd-refresh/"

# 2. Copy contracts into the fixture directory
cp .tmp/cc-sdd-refresh/feature-registry.yaml \
  skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/feature-registry.yaml

# 3. Update the pinned clone metadata
cp .tmp/cc-sdd-refresh/clone-metadata.json \
  skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/clone-metadata.json

# 4. Commit the updated fixtures
git add skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/
git commit -m "fix(reverse-engineer-rpi): update cc-sdd golden fixtures to <new-tag-or-sha>"
```

Fixture files that must be committed for the test to pass:

- `skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/clone-metadata.json`
- `skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/feature-registry.yaml`
- `skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/cli-surface-contracts.txt`
- `skills/reverse-engineer-rpi/fixtures/cc-sdd-v2.1.0/docs-features.txt`

## Script-Driven Workflow

Run:

```bash
python3 skills/reverse-engineer-rpi/scripts/reverse_engineer_rpi.py <product_name> --authorized [flags...]
```

This generates the required outputs under `output_dir/` and (when applicable) `.agents/council/` and `.agents/learnings/`.

## Outputs (MUST be generated)

Core outputs under `output_dir/`:
1. `feature-inventory.md`
2. `feature-registry.yaml`
3. `validate-feature-registry.py`
4. `feature-catalog.md`
5. `spec-architecture.md`
6. `spec-code-map.md`
7. `spec-cli-surface.md` (Node, Python, or Go CLI detected; otherwise a note is written to `spec-code-map.md`)
8. `spec-clone-vs-use.md`
9. `spec-clone-mvp.md` (original MVP spec; do not copy from target)
10. `clone-metadata.json` (when `--upstream-repo` is used; records resolved commit SHA)

Binary-mode extras:
- `binary-analysis.md` (best-effort summary)
- `binary-embedded-archives.md` (index only; no dumps)

Repo-mode extras:
- `spec-artifact-surface.md` (best-effort; template/manifest driven install surface)
- `artifact-registry.json` (best-effort; hashed template inventory when manifests/templates exist)

If `--security-audit`, also create `output_dir/security/`:
- `threat-model.md`
- `attack-surface.md`
- `dataflow.md`
- `crypto-review.md`
- `authn-authz.md`
- `findings.md`
- `reproducibility.md`
- `validate-security-audit.sh`

## Self-Test (Acceptance Criteria)

End-to-end fixture (safe, owned demo binary with embedded ZIP):

```bash
bash skills/reverse-engineer-rpi/scripts/self_test.sh
```

This must show:
- feature inventory generated
- registry generated
- registry validator exits 0
- in security mode: `validate-security-audit.sh` exits 0 and secret scan passes

## Examples

### Scenario: Reverse-Engineer an Open-Source CLI in Repo Mode

**User says:** `$reverse-engineer-rpi cc-sdd --mode=repo --upstream-repo="https://github.com/gotalab/cc-sdd.git" --upstream-ref=v1.0.0`

**What happens:**
1. The script shallow-clones the upstream repo at the pinned tag `v1.0.0` and records the resolved SHA in `clone-metadata.json`.
2. It scans the repo for CLI entry points, config/env surface, schema files, and artifact manifests, then writes `feature-inventory.md`, `feature-registry.yaml`, contract JSON, and all spec files under the output directory.

**Result:** A complete feature catalog and machine-checkable `feature-registry.yaml` are generated under `.agents/research/cc-sdd/`, ready for golden-fixture diffing.

### Scenario: Binary Analysis With Security Audit

**User says:** `$reverse-engineer-rpi ao --authorized --mode=binary --binary-path="$(command -v ao)" --security-audit`

**What happens:**
1. The script runs static analysis on the `ao` binary (file metadata, linked libraries, embedded archive signatures) and writes `binary-analysis.md` and `binary-embedded-archives.md`.
2. It generates the full security audit suite (`threat-model.md`, `attack-surface.md`, `findings.md`, etc.) under `output_dir/security/` and runs the secret-scan gate over all outputs.

**Result:** Binary analysis artifacts plus a validated security audit are produced; `validate-security-audit.sh` exits 0 confirming all security deliverables are present and secrets-clean.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Script refuses to run binary analysis | Missing `--authorized` flag | Add `--authorized` to confirm you have explicit written authorization to analyze the binary. |
| `clone-metadata.json` not generated | `--upstream-repo` was not provided | Pass `--upstream-repo` (and optionally `--upstream-ref`) to enable clone metadata tracking. |
| Fixture test diff fails unexpectedly | Upstream repo changed or golden fixtures are stale | Re-run with the pinned ref, copy fresh contracts into `fixtures/`, and commit the updated golden files (see Updating Fixtures). |
| `spec-cli-surface.md` not generated | No recognized CLI framework (Node/Python/Go) detected in the repo | Check that the target repo has a discoverable CLI entry point; otherwise the CLI surface is documented in `spec-code-map.md` instead. |
| Network error during repo clone | Firewall, VPN, or GitHub rate limit blocking the shallow clone | Verify network connectivity, authenticate with `gh auth login` if the repo is private, or use `--local-clone-dir` to point at a pre-cloned directory. |

## Local Resources

### scripts/

- `scripts/extract_docs_features.sh`
- `scripts/extract_sitemap_paths.sh`
- `scripts/fetch_url.py`
- `scripts/generate_feature_catalog_md.py`
- `scripts/generate_feature_inventory_md.py`
- `scripts/repo_fixture_test.sh`
- `scripts/reverse_engineer_rpi.py`
- `scripts/scaffold_feature_registry.py`
- `scripts/self_test.sh`
- `scripts/validate.sh`
- `scripts/validate_feature_registry.py`


