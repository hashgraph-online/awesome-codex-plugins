# Composable Security Suite Runbook

Use this reference for authorized binary assurance, baseline comparison, policy enforcement, and offline repo-surface redteam. The caller supplies authorization and owns every decision after the report.

## Primitive model

1. `collect-static` records file metadata, runtime heuristics, linked libraries, and embedded archive signatures.
2. `collect-dynamic` runs a sandboxed command (default `--help`) and records processes, file changes, and network endpoints.
3. `collect-contract` captures the binary's machine-readable command/help contract.
4. `compare-baseline` reports added, removed, and changed commands.
5. `enforce-policy` evaluates allow/deny rules and a severity verdict.
6. `collect-redteam` scans repo-owned control surfaces with the offline attack pack.
7. `run` composes the binary primitives and writes the suite summary.

## Commands

Capture an owned binary:

```bash
python3 skills/security/scripts/security_suite.py run \
  --binary "$(command -v ao)" \
  --out-dir .tmp/security-suite/ao-current
```

Compare with a known-good baseline:

```bash
python3 skills/security/scripts/security_suite.py run \
  --binary "$(command -v ao)" \
  --out-dir .tmp/security-suite/ao-current \
  --baseline-dir .tmp/security-suite/ao-baseline \
  --fail-on-removed
```

Enforce policy:

```bash
python3 skills/security/scripts/security_suite.py run \
  --binary "$(command -v ao)" \
  --out-dir .tmp/security-suite/ao-current \
  --policy-file skills/security/references/policy-example.json \
  --fail-on-policy-fail
```

Run offline redteam:

```bash
python3 skills/security/scripts/prompt_redteam.py scan \
  --repo-root . \
  --pack-file skills/security/references/agentops-redteam-pack.json \
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

The redteam scanner writes:

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
- `deny_network_endpoint_patterns`
- `block_if_removed_commands`
- `min_command_count`

Do not relax policy or refresh a baseline merely because a candidate fails. Classify the delta, preserve the failing artifact, and require explicit judgment for an intentional contract change.

## Redteam pack model

Start from `agentops-redteam-pack.json`. Cases use `globs`, `require_groups`, `forbidden_any`, and `applies_if_any` to bind adversarial prompts to repo-owned control surfaces. The shipped cases cover instruction precedence, context overexposure, destructive git misuse, security-gate bypass, unsafe shell, and secret handling.

## Triage

- Empty dynamic evidence: confirm the owned binary runs and supply an appropriate safe command.
- Zero captured commands: verify the binary exposes the expected help interface.
- Removed-command failure: inspect `compare/baseline-diff.json`; update the baseline only for an intentional accepted contract change.
- Policy failure: inspect `policy/policy-verdict.json`; change policy only with accountable approval.
- Redteam failure: determine whether the control regressed or the attack-pack matcher needs an intentional update.
