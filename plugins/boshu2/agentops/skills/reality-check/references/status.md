# Native status

Loaded by [Reality Check](../SKILL.md) when the caller asks for a status
snapshot.

Use `ao status` for the local evidence-store view, or
`ao status --evidence-root <dir>` for a protected external store. It validates
content-addressed intent and verdict artifacts before counting them, reports
corruption or unavailable sources, and shows evidence recency. Without
`--evidence-root` it reads `.agents/ao/intents/sha256` and
`.agents/ao/verdicts/sha256`; a count is not a per-artifact digest inventory.
Inspect a specific digest or timestamp only when that artifact is part of the
requested question.

Report caller-supplied subject manifests from their named location. Otherwise
mark manifests, runtime phase, elapsed execution, tool-call activity and
remaining work as not checked. An artifact's recent timestamp proves evidence
recency, not an active worker. Read other tracker, Git or factory facts only
from their own authorized source; do not blend factory completion, green checks
and a fresh verdict into one health judgment. Report unavailable evidence
explicitly.
