Submit the findings by calling `submit_findings(repo, pr, findings=[…])` (one call).
Each item matches the shared findings schema; the server validates and assigns ids.

If a finding cannot be tied to a specific line, use the closest changed line and
explain the scope in `message`.

If there are no meaningful findings, call `submit_findings` with an empty list and say so.

Write `message` and `suggestion` in the output language given by the orchestrator
(standalone: the user's language).
