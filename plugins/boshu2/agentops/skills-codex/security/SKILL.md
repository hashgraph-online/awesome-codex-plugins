---
name: security
description: Run authorized repository security scans for
---
# Security Skill

> **Purpose:** Run repeatable security checks across code, scripts, authorized binaries, and repo-managed prompt surfaces.

Use this skill for a caller-requested repository scan, authorized binary assurance, dependency risk, secrets, or offline prompt-surface redteam.

## Critical Constraints

- Scan only repositories, binaries, and prompt surfaces the operator owns or is explicitly authorized to assess. **Why:** a security review does not grant access to third-party systems or proprietary material.
- Keep collection read-only by default; do not exfiltrate secrets, execute destructive payloads, or mutate policy/baselines to manufacture green. **Why:** the assessment must not become the incident or erase its evidence.
- Treat missing/error scanners as a coverage gap, never a clean finding; use `--require-tools` when complete tool coverage is required. **Why:** absent evidence is not evidence of absence.
- Use the current agent and local shell; do not start another runtime or orchestration substrate unless explicitly requested. **Why:** repository scanning is a bounded operation, not permission to fan out.
- Run the selected scan once and report findings plus coverage gaps. Remediation,
  risk acceptance, reruns, and promotion are caller decisions.

## Security Surfaces

1. **Repository gate:** `scripts/security-gate.sh` composes available scanners for quick/full/release checks.
2. **Composable suite:** `scripts/security_suite.py` provides static, dynamic, contract, baseline, and policy primitives for authorized binaries.
3. **Offline redteam:** `scripts/prompt_redteam.py` checks repo-owned prompt and tool-control surfaces against the attack pack.

This is the canonical security runbook. Suite policy gating produces machine-consumable outputs, including `policy/policy-verdict.json` when a policy file is supplied.

Read [the suite runbook](references/security-suite-runbook.md) before binary, policy, baseline, or redteam work. Use [the OWASP checklist](references/owasp-checklist.md) for code-level review.

## Execution Workflow

### 1) Quick gate

Run:

```bash
scripts/security-gate.sh --mode quick
```

**Checkpoint:** preserve the exit code and verify the reported `security-gate-summary.json` exists and parses before triage.

### 2) Full scan

Run:

```bash
scripts/security-gate.sh --mode full
```

Add `--require-tools` when skipped scanners would invalidate the assurance claim. **Checkpoint:** report the result as incomplete unless the selected artifact validator and process both succeed.

### 3) Scheduled gate

Scheduled automation runs the full gate against the intended branch and retains its artifact directory. A failing scheduled run creates actionable tracked work; AgentOps itself does not supply the scheduler.

### 4) Hunt discipline

For review work beyond the scripted gates (code-level or redteam passes), hunt
against the full taxonomy, not your first hunch:

- **Full-taxonomy hunt.** Walk every applicable class in
  [the OWASP checklist](references/owasp-checklist.md) (or the attack pack for
  prompt surfaces) and record a per-class result: finding, clean, or
  not-assessed. An unvisited class is a coverage gap, not a clean. Chasing one
  suspicious lead to the exclusion of the taxonomy is the **first-scent
  fixation** failure mode.
- **Empirical proof per finding.** A finding is real when it reproduces: a
  concrete input, request, or command demonstrating the behavior, captured in
  the artifact. Pattern-match-only findings are reported as suspicions, ranked
  below proven ones.
- **Fail-open probes.** For every guard, gate, or timeout on the surface, ask
  what happens when it errors or hangs — then probe it where safe. A control
  that fails open under error is a finding even when its happy path is correct.
- **Identity-chain traces.** For authenticated or delegated flows, trace who
  the effective identity is at each hop (user, service, token, hook). A hop
  where identity is assumed rather than verified — the **borrowed identity**
  failure mode — is a finding.
- **Quiet-round convergence.** Iterate full passes until one complete pass
  yields nothing new: no new finding, no new coverage gap. That quiet round is
  the stop condition. Stopping after a loud round (findings still arriving) is
  premature; report the hunt as unconverged if the budget ends before a quiet
  round.

### 5) Triage

1. Open the latest artifact and identify scanner, severity, file, and coverage gaps.
2. Reproduce the finding with the narrowest safe command.
3. Rank concrete findings and preserve coverage gaps.
4. Stop. Remediation, risk acceptance, and any later scan are new caller decisions. Do not downgrade, suppress, or update a baseline merely to pass.

## Output Specification

**Artifact directory:** repository gates write `${SECURITY_GATE_OUTPUT_DIR:-${TMPDIR:-/tmp}/agentops-security}/<run-id>/`; composable-suite and redteam runs use their explicit `--out-dir`.

**Filename convention:** repository gates require `security-gate-summary.json` (and raw `summary.json`); suite runs require `suite-summary.json`; redteam runs require `redteam/redteam-results.json`.

**Serialization/schema format:** `security-gate-summary.json` is JSON with nonempty `mode`, `run_id`, `output_dir`, and `gate_status`, numeric `missing_tool_count`, boolean `require_tools`, and object `toolchain`.

**Validator command:** with `OUT=<security-gate-run-dir>`, run `jq -e '(.mode|type)=="string" and (.mode|length)>0 and (.run_id|type)=="string" and (.run_id|length)>0 and (.output_dir|type)=="string" and (.output_dir|length)>0 and .gate_status=="PASS" and (.missing_tool_count|type)=="number" and (.require_tools|type)=="boolean" and (.toolchain|type)=="object"' "$OUT/security-gate-summary.json" >/dev/null`.

**Output:** report the artifact path, command/exit code, mode, gate status,
missing-tool coverage, ranked findings, and authorization boundary. Do not add
an owner, next action, approval, release, or retry decision.

## Quality Checklist

- [ ] Target and authorization boundary are explicit; collection stayed within them.
- [ ] Scanner availability and skipped/error coverage are visible in the report.
- [ ] Findings include severity, location, reproducible evidence, and bounded remediation guidance.
- [ ] Artifacts contain no newly exposed secrets or unredacted sensitive payloads.
- [ ] The report distinguishes a passing scan from permission to promote or release.
- [ ] Suppressions, policy changes, baselines, and risk acceptance require explicit judgment.
- [ ] The report stops after evidence and contains no continuation decision.

## Validation

Run the skill and redteam validators:

```bash
bash skills/security/scripts/validate.sh
bash tests/scripts/test-security-suite-redteam.sh
```

For a bounded suite smoke test, use an owned binary and a temporary output directory as shown in [the suite runbook](references/security-suite-runbook.md).

## Examples

- A quick Security request runs the repository gate once and reports coverage and findings.
- A full Security request runs the full scan once and preserves its artifacts.
- An authorized binary request may capture a baseline in an explicit temporary output directory.
- A red-team request may run the offline attack pack over repo-owned surfaces.

## Troubleshooting

| Problem | Response |
|---------|----------|
| Scanner missing/error | Record the coverage gap; install it or rerun with `--require-tools` when required |
| Local/CI mismatch | Compare scanner versions, config, mode, and both artifact directories |
| Suspected false positive | Reproduce narrowly; document any authorized suppression and its owner |
| Suite/baseline failure | Inspect the named compare/policy artifact; never refresh baseline reflexively |
| Redteam failure after wording change | Decide whether the control regressed or the attack-pack matcher needs intentional revision |

## Reference Documents

- [references/security-suite-runbook.md](references/security-suite-runbook.md) — binary/policy/baseline/redteam commands and artifacts
- [references/security.feature](references/security.feature) — repository-gate executable spec
- [references/security-suite.feature](references/security-suite.feature) — composable-suite executable spec
- [references/owasp-checklist.md](references/owasp-checklist.md) — OWASP Top 10 review
- [references/agentops-redteam-pack.json](references/agentops-redteam-pack.json) — offline attack pack
- [references/policy-example.json](references/policy-example.json) — starter policy
