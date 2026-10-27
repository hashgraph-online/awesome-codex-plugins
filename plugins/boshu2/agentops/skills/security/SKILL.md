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

Use this skill for a caller-requested security review of code or of a plan or design before code exists, a repository scan, authorized binary assurance, dependency risk, secrets, or offline prompt-surface redteam.

## Critical Constraints

- Scan only repositories, binaries, and prompt surfaces the operator owns or is explicitly authorized to assess. **Why:** a security review does not grant access to third-party systems or proprietary material.
- Keep collection read-only by default; do not exfiltrate secrets, execute destructive payloads, or mutate policy/baselines to manufacture green. **Why:** the assessment must not become the incident or erase its evidence.
- Treat missing/error scanners as a coverage gap, never a clean finding; use `--require-tools` when complete tool coverage is required. **Why:** absent evidence is not evidence of absence.
- Use the current agent and local shell; do not start another runtime or orchestration substrate unless explicitly requested. **Why:** repository scanning is a bounded operation, not permission to fan out.
- Report findings and coverage gaps, then stop. Remediation, risk acceptance,
  reruns, promotion, and any ship or merge call are caller decisions. Asked
  whether to ship, merge or deploy, give the findings and coverage, then say in
  one line that the go/no-go on that evidence is the caller's; recommending
  ship, hold or block in any wording is that decision. Name each finding's
  remediation class in a few words; do not write the patch, a plan, an owner,
  or a priority.

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
   [the class checklist](references/owasp-checklist.md), plus fail-open,
   identity and any class the surface needs that the list lacks, and give each
   a result: finding, clean, or not assessed. An unvisited class is a gap, never a clean.
   Chasing one lead to the exclusion of the taxonomy is the **first-scent
   fixation** failure mode.
4. **Proven versus suspected.** A finding is proven only when you ran a
   concrete input, request, or command and observed the behavior; capture it.
   A finding reasoned from the code is suspected, even with a candidate input;
   give that input and rank it below proven findings.
5. **Snapshot scope.** Name the exact snapshot (commit, working tree on a
   stated HEAD, or document revision) and the path scope. List inputs you did
   not read separately as unread, deleted or outside scope; none of them counts
   as clean. Keep impact inside the snapshot: a finding that needs absent code,
   a future change or an unread path is a hypothesis and is labeled so. When
   the remaining budget cannot finish another full pass, stop opening new leads
   and report the hunt as unconverged.
6. **Shipped scope for a share or publish question.** When asked whether
   content is safe to make public or hand to another party (a repository, an
   export, a package), the snapshot is what the recipient will receive: the
   built artifact or output tree, every commit reachable in the history that
   travels with it, and derived copies such as indexes, caches and generated
   files. Content removed at HEAD is still exposed in earlier commits. Report
   history exposure with its fix class (credential rotation, fresh history or
   an owner-authorized rewrite) and perform none of them.

For each finding, explain the attacker path and relevant protective control in
the fields below. Read [attacker-path evidence](references/attacker-path-evidence.md)
only when reachability, control effectiveness, or claimed test completion needs
closer support for that finding.

```text
target:   <paths, endpoints, or binary>; authorization: <boundary>
snapshot: <commit | working tree on HEAD | document revision>; unread: <paths> | deleted: <paths> | outside scope: <paths>
findings: <id> <severity> <file:line> <class>: <what>
          proven: <input run> | suspected: <candidate input, why not run>
          path: <attacker input> -> <reachable behavior> -> <trust boundary> -> <impact>
          control: <relevant protection challenged and outcome, or none identified>
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

A plan, spec or design with no code yet gets the same hunt, aimed at what the
document proposes. List the endpoints, data stores, integrations and inputs it
adds, then report only weaknesses an attacker could use if it is built as
written, such as a capability with no named actor or access decision; sensitive
data whose handling in transit, at rest, in logs or at deletion is unstated; a
third party or secret whose trust, storage, rotation or compromise behavior is
unstated; or a stated choice, including how an input is handled, that is itself
unsafe. Cite the section. A weakness in what the document proposes is inside
its revision, not a rule-5 hypothesis; with nothing to run, each is suspected.

## Scripted scans

Each selected scan runs once per request; a rerun is a new caller decision.

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows it
as "Base directory for this skill"; Codex lists this skill's SKILL.md path; in
an AgentOps source checkout it is `skills/security`. Replace `<skill-dir>` with
that absolute path before running a command. The working directory stays the
user's repository. If the host did not show where this skill is installed, use
the directory of the SKILL.md you read. If you cannot determine it, do not guess
a path or run a same-named script from the current repository; say the bundled
script is unavailable and run the scanners the project already uses, record the
suite or redteam scan as a coverage gap, and do the manual hunt.

| Surface | Entry point | Location |
|---|---|---|
| Repository gate (quick or full) | `bash scripts/security-gate.sh` | AgentOps repository root only |
| Composable suite for authorized binaries | `python3 "<skill-dir>/scripts/security_suite.py"` | bundled with this skill |
| Offline prompt-surface redteam | `python3 "<skill-dir>/scripts/prompt_redteam.py"` | bundled with this skill |

- **No gate script** (any other repository): run the scanners the project
  already uses, such as a dependency audit, secret scan, or static analyzer,
  record each one that is absent as a coverage gap, and do the manual hunt.
- **Redteam pack:** the bundled [attack pack](references/agentops-redteam-pack.json)
  targets AgentOps control surfaces. In another repository its cases fail with
  "no files matched target globs"; that is a pack mismatch, not a finding. A
  PASS shows the controls are written down, not that an agent resists them.
- Read [the suite runbook](references/security-suite-runbook.md) before gate,
  binary, policy, baseline, or redteam work. It holds the commands, the gate's
  exit codes, the artifact contracts, and the limits of the dynamic run, which
  is sampled and not isolated.

### Triage

1. Open the latest artifact and identify scanner, severity, file, and coverage gaps.
2. Reproduce the finding with the narrowest safe command; an unreproduced hit stays suspected.
3. Rank concrete findings and preserve coverage gaps.
4. Stop. Remediation, risk acceptance, and any later scan are new caller decisions. Do not downgrade, suppress, or update a baseline merely to pass.

## Output Specification

- **Artifact directory:** suite and redteam runs write under their explicit
  `--out-dir`; the repository gate's directory is in the runbook.
- **Filename convention:** `security-gate-summary.json` (gate),
  `suite-summary.json` (suite), `redteam/redteam-results.json` (redteam).
- **Serialization/schema format:** JSON. **Validator command:** the gate
  summary's field contract and `jq` check are in the runbook; a summary that
  fails it makes the result incomplete.

**Downstream handoff:** the review report above; for scripted scans also the
artifact path, command and exit code, mode, and gate status. The
report stops after evidence: no owner, next action, approval, release, ship,
or retry decision, and no newly exposed secret or unredacted sensitive payload.
