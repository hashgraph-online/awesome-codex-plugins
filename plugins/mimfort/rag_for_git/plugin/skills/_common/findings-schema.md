Findings output schema (shared). The calling skill sets `category`.

Submit findings by calling `submit_findings(repo, pr, findings=[…])` — one call,
each item matching this per-finding schema (the server validates against it and
assigns a stable id). Do NOT return findings as prose/JSON text.

```json
[{
  "category": "<set by the calling skill>",
  "severity": "low|medium|high|critical",
  "file": "<path of the reviewed file>",
  "line": <line number in the NEW file, or null>,
  "side": "RIGHT|LEFT",
  "code_quote": "<exact line from the new file, or null when line is null>",
  "message": "<what is wrong and why it matters>",
  "suggestion": "<short advice or null>",
  "fix": {"start_line": N, "end_line": M, "replacement": "<new code>"} | null,
  "confidence": 0.0
}]
```

Field semantics:
- `category` — set by the calling skill (see its own instructions).
- `severity` — `low|medium|high|critical`.
- `file` — path of the reviewed file.
- `line` — line number in the NEW file, or `null` (a null line lands in the summary, not inline).
- `side` — `RIGHT` (new version) or `LEFT` (old version).
- `code_quote` — exact line copied verbatim from the NEW file; it grounds the line number. `null` only when `line` is null. An inaccurate quote is worse than no quote.
- `message` / `suggestion` — written in the orchestrator's output language.
- `fix` — exact replacement for a contiguous line range in the new file (`start_line`/`end_line`/`replacement`), or `null` when unsure.
- `confidence` — float `0.0..1.0`; it feeds the publish gate (`min_confidence`),
  so be honest. Calibrate against grounding + reproducibility:
  - 0.8–1.0 — grounded AND verified: an exact `code_quote` from the new file AND
    the problem is confirmed via tools (read_file/search_code showed the handling
    is truly absent / the call graph confirms the impact). An unambiguous, real defect.
  - 0.5–0.7 — grounded but context-dependent: a valid `code_quote`, the issue is
    plausible, but reproducibility depends on runtime data / unchecked branches /
    caller context. Phrase as "verify that…", not a categorical claim.
  - ≤ 0.4 — speculative: no solid grounding, not verified with tools, or a guess about
    intent. Below the 0.5 gate → it will be dropped. Prefer dropping it yourself
    (an empty findings list is valid).

Write `message` and `suggestion` in the output language given by the orchestrator.
