# Durable premortem review

Loaded by [Premortem](../SKILL.md) only when the caller requests a durable,
machine-readable review instead of the inline findings.

`<skill-dir>` is the directory that contains Premortem's SKILL.md. Claude Code shows it
as "Base directory for this skill"; Codex lists this skill's SKILL.md path; in
an AgentOps source checkout it is `skills/premortem`. Replace `<skill-dir>` with
that absolute path before running a command. The working directory stays the
user's repository. If the host did not show where this skill is installed, use
the directory of the Premortem SKILL.md you read. If you cannot determine it, do not guess
a path or run a same-named script from the current repository; say the bundled
script is unavailable and check the review's fields by hand against its
[schema](../schemas/premortem-plan-review.v1.schema.json).

When the caller requests a durable review, return `premortem-plan-review.v1`
and check it with `bash "<skill-dir>/scripts/validate-output.sh" <review.json>`. Its
`intent_digest` is the 64-hex SHA-256 of the exact intent text as supplied:
`shasum -a 256 plan.md | cut -d' ' -f1` for a file, or
`printf '%s' "$TEXT" | shasum -a 256 | cut -d' ' -f1` for pasted text.
`author_context_id` names who wrote the plan (the caller, or that session's ID)
and `judge_context_id` names this context. The form has no fields for verifiers
or step marks, so it is lossy: record each inline `Verifiers:` and `Steps:` line
verbatim in `checked`, and put each finding's construction or blocking fact in
its `evidence`. The validator rejects identical author and judge IDs but
checks only that the strings differ, not that an independent judge ran, so a
review without one stays inline.
