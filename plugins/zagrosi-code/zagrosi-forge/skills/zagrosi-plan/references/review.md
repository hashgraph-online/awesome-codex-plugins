# Review

Review material requirement/ownership gaps, security, data integrity, compatibility,
concurrency/retry, recovery, test adequacy, and unnecessary complexity. Match
scrutiny to [depth](depth-standards.md); independent perspectives need a concrete risk.

Write `## Review` in the canonical artifact with literal
`Reviewed: <concrete scope, evidence, and result>`, findings
(`severity: problem -> fix`), resolutions, and residual risks. Finish with
`Verdict: pass.` or `Verdict: fixed.`; a verdict alone is insufficient. Blocked
findings prevent admission. Apply fixes to their owning contracts.

Legacy `reviews/codex.md` and separate reviews remain supported; never duplicate
them merely to satisfy artifact count. Re-review changed risks only.
