# Review

The active agent owns review in either host; a second model CLI is optional.
For selected external providers/models, follow the shared
[provider review protocol](../../zagrosi-forge/references/providers.md).

Review material requirement/ownership gaps, security, data integrity, compatibility,
concurrency/retry, recovery, test adequacy, and unnecessary complexity. Match
scrutiny to [depth](depth-standards.md); independent perspectives need a concrete risk.
Compare assumptions with the unchanged source brief: they cannot narrow its
promises. For refactors, map promised caller surfaces to baseline regressions.
Where coverage is uncertain, identify a plausible wrong result and a check that
distinguishes it; keep this in the existing Contract/Review. Check proposed
boundaries and any deferral of encountered cleanup.

Write `## Review` in the canonical artifact with literal
`Reviewed: <concrete scope, evidence, and result>`, findings
(`severity: problem -> fix`), resolutions, and residual risks. Finish with
`Verdict: pass.` or `Verdict: fixed.`; a verdict alone is insufficient. Blocked
findings prevent admission. Apply fixes to their owning contracts.

Legacy `reviews/codex.md` and separate reviews remain supported; never duplicate
them merely to satisfy artifact count. Re-review changed risks only.
