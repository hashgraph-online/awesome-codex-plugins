# Assessment Delegation and Decision Record

Use this record before running an assessment. It names who owns each step so the audit agent does not silently become the owner of arithmetic, command safety, or an irreversible decision.

## Delegation map

| Step | Owner | Reversibility / stakes | Accountability | Detection mechanism |
|---|---|---|---|---|
| Interpret repository structure and evidence | Audit agent | Reversible analysis; an unsupported conclusion can misdirect a repair backlog. | The audit agent must cite evidence and label uncertainty. | Every repository claim carries a path and line or command result; any uncited claim is rejected in report review. Owner: report reviewer. |
| Execute approved commands, calculate totals, and validate report shape | Deterministic tooling | Commands may create local artifacts; a wrong score or malformed report makes a decision unreliable. | The audit agent selects only safe commands and records their result. | The command inventory contains every executed command; the validator must exit `0`; score addends must differ from the stated raw total by `0`. Owner: audit agent. |
| Set scope constraints and approve irreversible actions | Human | Irreversible or external actions can change customer, production, or shared state. | The requesting human owns scope and authorization. | Stop before any irreversible, external-write, privileged, paid, or otherwise unclassified action; no such command may appear as executed without approval. Owner: requesting human. |

## Decision records

### Command execution

**Decision:** Classify each command and execute only `local-read` or safe `local-build` work without additional approval.

**Cost:** Command classification and recording add a small amount of audit time.

**Complexity:** The agent must keep a command inventory and clean up only artifacts it created.

**Risk:** A command can mutate state or contact an external system despite looking routine.

**Detection mechanism:** The Commands Executed inventory is reviewed for every command with a non-local safety class; threshold: `0` unapproved external-write, privileged, paid, or unclassified commands. Owner: report reviewer.

### Score calculation

**Decision:** Calculate raw totals, applicable maximum, and normalized score with deterministic tooling, not model arithmetic.

**Cost:** One local calculation command per report.

**Complexity:** The agent must preserve the scorecard addends and record the calculation inputs.

**Risk:** A transcription or arithmetic error can produce a plausible but incorrect readiness status.

**Detection mechanism:** Re-add the scorecard values with a local calculation; threshold: stated raw total and normalized score differ by `0` from the calculated values. Owner: audit agent.

### Report validation

**Decision:** Run `python3 <skill-directory>/scripts/validate_report.py reports/agentic-readiness.md` after the provisional report write, where `<skill-directory>` contains this skill's `SKILL.md`.

**Cost:** A local Python process and, at most, one corrective rewrite.

**Complexity:** The report must retain the fixed headings, Run and Scope keys, and glossary shape the validator checks, then use the bounded finalization rewrite to record the validator result.

**Risk:** A malformed report can look complete while breaking automated consumption or audit comparison.

**Detection mechanism:** Validator process exit status; threshold: exit code must be `0` after at most one corrective rewrite. Owner: audit agent.
