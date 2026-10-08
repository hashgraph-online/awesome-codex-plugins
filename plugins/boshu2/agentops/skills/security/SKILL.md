---
name: security
description: 'Review code for security problems; scan for vulnerabilities, secrets, dependency and prompt risks. Use when: asked whether code is safe to ship, even one small handler.'
practices:
- supply-chain-integrity
- design-by-contract
- sre
hexagonal_role: driven-adapter
consumes:
- repo-context
produces:
- security-gate-summary.json
- suite-summary.json
- redteam-results.json
context_rel:
- kind: supplier-to
  with: validate
skill_api_version: 1
user-invocable: true
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
metadata:
  capabilities: [security]
  effects: [write_scan_artifacts]
  canonical_status: canonical
  disposition: keep_specialist
  graph_root: true
  tier: product
  dependencies: []
output_contract: 'stdout: security scan report'
---
# Security Skill

> **Purpose:** Find and report security weaknesses in code, scripts, authorized binaries, and repo-managed prompt surfaces, with honest coverage.

Use this skill for a caller-requested security review of code, a repository scan, authorized binary assurance, dependency risk, secrets, or offline prompt-surface redteam.

## Critical Constraints

- Scan only repositories, binaries, and prompt surfaces the operator owns or is explicitly authorized to assess. **Why:** a security review does not grant access to third-party systems or proprietary material.
- Keep collection read-only by default; do not exfiltrate secrets, execute destructive payloads, or mutate policy/baselines to manufacture green. **Why:** the assessment must not become the incident or erase its evidence.
- Treat missing/error scanners as a coverage gap, never a clean finding; use `--require-tools` when complete tool coverage is required. **Why:** absent evidence is not evidence of absence.
- Use the current agent and local shell; do not start another runtime or orchestration substrate unless explicitly requested. **Why:** repository scanning is a bounded operation, not permission to fan out.
- Report findings and coverage gaps, then stop. Remediation, risk acceptance,
  reruns, promotion, and any ship or merge call are caller decisions. Name each
  finding's remediation class in a few words; do not write the patch, a plan,
  an owner, or a priority.

## What every review reports

Apply these to every review, scripted or manual. They are the rules most often skipped:

1. **Fail-open paths.** For every guard, check, timeout, and exception handler
   on the surface, ask what happens when it errors or hangs. A control that
   grants access, skips a check, or continues as success on error is a finding
   even when its happy path is correct.
2. **Borrowed identity.** Trace the effective identity at each hop (user,
   service, token, default, hook). A hop where identity is assumed, defaulted,
   or inherited instead of verified is the **borrowed identity** failure mode
   and a finding.
3. **Per-class coverage ledger.** Walk every applicable class in
   [the OWASP checklist](references/owasp-checklist.md) (the attack pack for
   prompt surfaces), plus fail-open and identity, and give each a result:
   finding, clean, or not assessed. An unvisited class is a gap, never a clean.
   Chasing one lead to the exclusion of the taxonomy is the **first-scent
   fixation** failure mode.
4. **Proven versus suspected.** A finding is proven only when you ran a
   concrete input, request, or command and observed the behavior; capture it.
   A finding reasoned from the code is suspected, even with a candidate input;
   give that input and rank it below proven findings.

```text
target:   <paths, endpoints, or binary>; authorization: <boundary>
findings: <id> <severity> <file:line> <class>: <what>
          proven: <input run> | suspected: <candidate input, why not run>
          fix class: <a few words>
coverage: <class> -> finding <ids> | clean | not assessed (<why>)
tools:    <scanner or command> -> ran | missing | error
hunt:     converged after <n> passes | unconverged | not run
```

## Manual hunt

Code-level review and redteam passes work in any repository, with or without
AgentOps tooling. Walk the ledger against the full surface and probe fail-open
behavior where that is safe. Repeat full passes until one complete pass adds no
new finding and no new coverage gap; that quiet round is the stop condition. If
the budget ends first, report the hunt as unconverged. The quiet-round rule
applies only to the manual hunt.

## Scripted scans

Each selected scan runs once per request; a rerun is a new caller decision.

| Surface | Entry point | Location |
|---|---|---|
| Repository gate (quick or full) | `scripts/security-gate.sh` | AgentOps repository root only |
| Composable suite for authorized binaries | `skills/security/scripts/security_suite.py` | this skill's `scripts/` |
| Offline prompt-surface redteam | `skills/security/scripts/prompt_redteam.py` | this skill's `scripts/` |

- **No gate script** (any other repository): run the scanners the project
  already uses, such as a dependency audit, secret scan, or static analyzer,
  record each one that is absent as a coverage gap, and do the manual hunt.
- **Redteam pack:** the bundled [attack pack](references/agentops-redteam-pack.json)
  targets AgentOps control surfaces. In another repository its cases fail with
  "no files matched target globs"; that is a pack mismatch, not a finding.
- Read [the suite runbook](references/security-suite-runbook.md) before binary,
  policy, baseline, or redteam work.

This is the canonical security runbook. Suite policy gating produces machine-consumable outputs, including `policy/policy-verdict.json` when a policy file is supplied.

### Repository gate

```bash
scripts/security-gate.sh --mode quick   # changed scope
scripts/security-gate.sh --mode full    # repository-wide
```

Add `--require-tools` when skipped scanners would invalidate the assurance
claim. **Checkpoint:** preserve the exit code and verify the reported
`security-gate-summary.json` exists and parses before triage; report the result
as incomplete unless the selected artifact validator and process both succeed.

Scheduled automation runs the full gate against the intended branch and retains its artifact directory. A failing scheduled run creates actionable tracked work; AgentOps itself does not supply the scheduler.

### Triage

1. Open the latest artifact and identify scanner, severity, file, and coverage gaps.
2. Reproduce the finding with the narrowest safe command; an unreproduced hit stays suspected.
3. Rank concrete findings and preserve coverage gaps.
4. Stop. Remediation, risk acceptance, and any later scan are new caller decisions. Do not downgrade, suppress, or update a baseline merely to pass.

## Output Specification

**Artifact directory:** repository gates write `${SECURITY_GATE_OUTPUT_DIR:-${TMPDIR:-/tmp}/agentops-security}/<run-id>/`; composable-suite and redteam runs use their explicit `--out-dir`.

**Filename convention:** repository gates require `security-gate-summary.json` (and raw `summary.json`); suite runs require `suite-summary.json`; redteam runs require `redteam/redteam-results.json`.

**Serialization/schema format:** `security-gate-summary.json` is JSON with nonempty `mode`, `run_id`, `output_dir`, and `gate_status`, numeric `missing_tool_count`, boolean `require_tools`, and object `toolchain`.

**Validator command:** with `OUT=<security-gate-run-dir>`, run `jq -e '(.mode|type)=="string" and (.mode|length)>0 and (.run_id|type)=="string" and (.run_id|length)>0 and (.output_dir|type)=="string" and (.output_dir|length)>0 and .gate_status=="PASS" and (.missing_tool_count|type)=="number" and (.require_tools|type)=="boolean" and (.toolchain|type)=="object"' "$OUT/security-gate-summary.json" >/dev/null`.

**Output:** the review report above; for scripted scans also the artifact
path, command/exit code, mode, and gate status. Do not add an owner, next
action, approval, release, ship, or retry decision.

## Quality Checklist

- [ ] Target and authorization boundary are explicit; collection stayed within them.
- [ ] Every applicable class has a result; unvisited classes are listed as not assessed.
- [ ] Scanner availability and skipped/error coverage are visible in the report.
- [ ] Findings include severity, location, proven-or-suspected evidence, and a remediation class, with no patch, plan, owner, or priority.
- [ ] Artifacts contain no newly exposed secrets or unredacted sensitive payloads.
- [ ] The report distinguishes a passing scan from permission to promote, ship, or release.
- [ ] Suppressions, policy changes, baselines, and risk acceptance require explicit judgment.
- [ ] The report stops after evidence and contains no continuation decision.

## Validation

Run the skill and redteam validators:

```bash
bash skills/security/scripts/validate.sh
bash tests/scripts/test-security-suite-redteam.sh
```

For a bounded suite smoke test, use an owned binary and a temporary output directory as shown in [the suite runbook](references/security-suite-runbook.md).

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
