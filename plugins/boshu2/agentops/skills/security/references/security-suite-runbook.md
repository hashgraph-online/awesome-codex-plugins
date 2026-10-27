# Security Suite Runbook

Use this reference for the AgentOps repository gate, authorized binary assurance, baseline comparison, policy enforcement, and offline repo-surface redteam. The caller supplies authorization and owns every decision after the report. The repository gate and the maintainer checks run from an AgentOps checkout root; the suite and redteam commands run from the repository under review, with `<skill-dir>` as defined in [SKILL.md](../SKILL.md).

## Repository gate (AgentOps repository root only)

```bash
bash scripts/security-gate.sh --mode quick   # changed scope
bash scripts/security-gate.sh --mode full    # repository-wide
```

Add `--require-tools` when skipped scanners would invalidate the assurance claim. **Checkpoint:** preserve the exit code and check `security-gate-summary.json` with the validator below before triage.

- Exit 2 (`BLOCKED_CRITICAL`) and exit 3 (`BLOCKED_HIGH`) are completed scans with blocking findings, not failed runs.
- Exit 4 means `--require-tools` was set and a scanner was missing or errored. The gate exits 4 before it passes on exit 2 or 3, so still read `gate_status` and `toolchain.findings` from the summary and report both the blocking findings and the incompleteness.
- Report the result as incomplete when the validator fails, on exit 4, or on any other nonzero exit (bad arguments, a missing toolchain script, or toolchain output that was not JSON).

**Artifact directory:** `${SECURITY_GATE_OUTPUT_DIR:-${TMPDIR:-/tmp}/agentops-security}/<run-id>/`, holding `security-gate-summary.json` and the raw `summary.json`.

**Schema:** `security-gate-summary.json` is JSON with nonempty `mode`, `run_id`, and `output_dir`, a `gate_status` of `PASS`, `WARN_QUALITY`, `BLOCKED_HIGH`, or `BLOCKED_CRITICAL`, numeric `missing_tool_count`, boolean `require_tools`, and object `toolchain`.

**Validator command:** with `OUT=<security-gate-run-dir>`, run `jq -e '(.mode|type)=="string" and (.mode|length)>0 and (.run_id|type)=="string" and (.run_id|length)>0 and (.output_dir|type)=="string" and (.output_dir|length)>0 and (.gate_status|IN("PASS","WARN_QUALITY","BLOCKED_HIGH","BLOCKED_CRITICAL")) and (.missing_tool_count|type)=="number" and (.require_tools|type)=="boolean" and (.toolchain|type)=="object"' "$OUT/security-gate-summary.json" >/dev/null`.

The validator proves the artifact is complete, not that the scan was clean; a scan
that found issues still passes it. Read the result from `gate_status`: `PASS`
means the scanners that ran reported no blocking findings and no high-severity
quality findings, `WARN_QUALITY` means only non-blocking quality findings,
`BLOCKED_HIGH` means high-severity security findings, and `BLOCKED_CRITICAL`
means critical findings, which in full mode also count failing pytest and go
test runs and a pytest run that errored or could not start; read
`toolchain.tools` and `toolchain.findings` for the cause. The gate writes
`UNKNOWN` when the toolchain summary carried no status, and the validator
rejects it.

## Primitive model

1. `collect-static` records file metadata, runtime heuristics, linked libraries, and embedded archive signatures.
2. `collect-dynamic` runs the binary (default `--help`) with HOME, TMPDIR, and the working directory redirected to scratch directories under `--out-dir` and the environment reduced to PATH, HOME, TMPDIR, and LANG. It is not isolated: there is no filesystem or network containment, so run only owned, trusted binaries. It records processes, file changes, and network endpoints:
   - file changes cover only the redirected HOME and working directories; a write to any other absolute path is not seen, so a clean result there is not a filesystem-wide clean;
   - processes and sockets are sampled every 0.2 seconds, so short-lived children and connections can be missed; an empty list means "not observed" and is a coverage gap, not "no network".
3. `collect-contract` captures the binary's command/help contract, including Cobra command groups.
4. `compare-baseline` reports added and removed commands and a runtime change.
5. `enforce-policy` evaluates allow/deny rules and a severity verdict.
6. `prompt_redteam.py scan`, a separate script, checks repo-owned control surfaces against the offline attack pack.
7. `run` composes the binary primitives and writes the suite summary.

## Commands

Capture an owned binary:

```bash
python3 "<skill-dir>/scripts/security_suite.py" run \
  --binary "$(command -v ao)" \
  --out-dir .tmp/security-suite/ao-current
```

Compare with a known-good baseline:

```bash
python3 "<skill-dir>/scripts/security_suite.py" run \
  --binary "$(command -v ao)" \
  --out-dir .tmp/security-suite/ao-current \
  --baseline-dir .tmp/security-suite/ao-baseline \
  --fail-on-removed
```

Enforce policy:

```bash
python3 "<skill-dir>/scripts/security_suite.py" run \
  --binary "$(command -v ao)" \
  --out-dir .tmp/security-suite/ao-current \
  --policy-file "<skill-dir>/references/policy-example.json" \
  --fail-on-policy-fail
```

Run offline redteam:

```bash
python3 "<skill-dir>/scripts/prompt_redteam.py" scan \
  --repo-root . \
  --pack-file "<skill-dir>/references/agentops-redteam-pack.json" \
  --out-dir .tmp/security-suite-redteam
```

## Artifact inventory

The binary suite writes beneath `--out-dir`:

- `static/static-analysis.json`
- `dynamic/dynamic-analysis.json`
- `contract/contract.json`
- `compare/baseline-diff.json` when a baseline is supplied
- `policy/policy-verdict.json` when a policy is supplied
- `suite-summary.json`

`run` exits 4 when `--fail-on-removed` or `--fail-on-policy-fail` fires, and `enforce-policy` alone exits 3 on a FAIL verdict. The redteam scanner writes:

- `redteam/redteam-results.json`
- `redteam/redteam-results.md`

Preserve command exit codes with the artifacts. A missing optional compare/policy artifact is valid only when that phase was not requested.

## Policy model

Start from `policy-example.json`. Supported checks include:

- `required_top_level_commands`
- `deny_command_patterns`
- `max_created_files`
- `forbid_file_path_patterns`
- `allow_network_endpoint_patterns`
- `deny_network_endpoint_patterns` (each endpoint is an lsof row; match the remote side after `->`, as the example does for private ranges)
- `block_if_removed_commands`
- `min_command_count` (zero captured commands is a FAIL when this is above 0, since every command check would be vacuous)

Do not relax policy or refresh a baseline merely because a candidate fails. Classify the delta, preserve the failing artifact, and require explicit judgment for an intentional contract change.

## Redteam pack model

Start from `agentops-redteam-pack.json`. Cases use `globs`, `require_groups`, `forbidden_any`, and `applies_if_any` to bind adversarial prompts to repo-owned control surfaces. The shipped cases cover instruction precedence, context overexposure, destructive operations, security-gate bypass, unsafe shell and secrets, and policy-gated suite outputs. The scan checks that each control is stated in the targeted files; it sends no prompt to a model, so a PASS shows the controls are written down, not that an agent resists the attack.

## Triage

- Scanner missing or errored: record the coverage gap; install it or rerun with `--require-tools` when complete coverage is required.
- Local and CI results differ: compare scanner versions, config, mode, and both artifact directories.
- Suspected false positive: reproduce narrowly; document any authorized suppression and its owner.
- Empty dynamic evidence: confirm the owned binary runs and supply an appropriate safe command; report what was not observed as a gap.
- Zero captured commands: verify the binary exposes the expected help interface.
- Removed-command failure: inspect `compare/baseline-diff.json`; update the baseline only for an intentional accepted contract change.
- Policy failure: inspect `policy/policy-verdict.json`; change policy only with accountable approval.
- Redteam failure: determine whether the control regressed or the attack-pack matcher needs an intentional update.

## Maintainer checks (AgentOps checkout only)

These need the AgentOps repository and are not part of a review in another repository:

```bash
bash skills/security/scripts/validate.sh
bash tests/scripts/test-security-suite-redteam.sh
```
