# Attacker-path evidence

Use this reference when a finding's reachability, protective control, or claimed
test completion needs closer support. Explain that finding in the existing
Security report. This reference grants no additional target access or execution
authority and requires no separate report.

## Connect the path

Identify the field or channel the attacker controls and any required access.
Trace it through reachable behavior to the intended trust boundary, then name
the concrete impact. Cite the relevant source locations and the protective
control challenged, when one applies. Mark an unknown hop as unknown; a scanner
label, dangerous API, or missing hardening cannot fill it in.

Read relevant callers, validation, middleware, and configuration far enough to
check that precise claim. Record counterevidence, including a guard that blocks
the candidate path. Do not turn an untraced alternative into a demonstrated bypass.

## Keep evidence claims separate

| Evidence | What it supports |
|---|---|
| Static source trace | A code-reasoned path and its assumptions; the finding stays suspected. |
| Actual reproduction | The exact input run and observed boundary violation and impact; this supports proven for that behavior only. |
| Legitimate-access control | Intended access or behavior works for the tested case. |
| Protective-control result | Whether the named guard blocks the stated path; distinguish source reasoning from an observed outcome. |
| Authorized repair check | The recorded check passes on the identified repair candidate; it does not retroactively prove the original finding. |
| Runner/assertion completion | The identified runner reached and completed the intended assertion; keep this distinct from a successful command exit. |
| Externally trustworthy evidence | A witness outside the target's control supports the exact observation it recorded, within its stated limits. |

A code-reasoned finding remains suspected even with a plausible candidate input.
Keep the existing per-class coverage ledger. A blocked path can inform coverage
without counting as a vulnerability; unexplored paths remain not assessed.

## Reproduce only within authority

Before a safe reproduction, confirm the target, allowed input, access, and effects
fit the caller's authorization. Capture the exact case, observation, and limits
without exposing secrets or sensitive payloads. If safe execution is unavailable,
report the source reasoning and why the candidate was not run; do not expand
access or execute an unsafe payload to upgrade the label.

Distinguish a denied adversarial case from an application that never started,
a generic error, or a skipped assertion. Use an authorized legitimate-access
case as a control when it helps interpret the boundary. A legitimate success
alone does not establish that unauthorized access is prevented.

## Interpret completion and repair evidence

A target printing `all security tests passed` does not authenticate adversarial
suite completion. Target-controlled output, counts, hashes, and exit codes are
diagnostics; they do not show that every intended assertion ran to completion.
Name who controlled the runner and evidence, and report unavailable completion
or witness evidence as a gap. Trust an external observation only for what that
observer could actually verify.

Prompt wording and the existing scan scripts do not promise authenticated test
completion, containment, or sandbox enforcement. State an actual verified
boundary or leave it unverified; do not infer one from the method's instructions.

A scan does not authorize repair or risk acceptance. Separately authorized
repairs remain the native caller's work. When such checks are later supplied,
keep original reproduction, repair identity, protective-control result,
legitimate behavior, and runner completion separate. A changed assertion,
removed feature, or disappearing warning alone does not demonstrate a repair.
Report findings and coverage gaps, then stop under the Security contract.

## Check the explanation against these cases

- A command-launch operation sits behind an effective input guard. The risky
  operation alone is unsupported as a vulnerability. If the route around the
  guard is untraced, retain that candidate as suspected with the missing hop;
  do not claim a proven bypass.
- A resource lookup accepts a caller-supplied record ID. A cross-tenant finding
  names that input, the lookup path, the tenant boundary crossed, and the other
  tenant's exposed content. Access to the caller's own record is a legitimate
  control, not evidence of the boundary violation.
- A target emits a success message and exits zero while assertion completion
  is unobserved. Record those diagnostics and the completion gap; do not claim
  that the adversarial suite completed.
