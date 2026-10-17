# Synthesis

Load this reference for Phase 4 and Phase 5. The completion checklist and the mechanical gate stay in `SKILL.md`.

## Phase 4 - Synthesize

After convergence and all verifications, read `INDEX.md` first, then open only the wave, verify, and ledger files the themes you are actually writing cite. The index exists so that synthesis does not require pulling the whole journal back into context; go to a wave file when a specific claim needs its detail, not by default. Then write `SYNTHESIS.md`:

```text
# Superloopy Research Synthesis: <query>
Workers: <total> · Waves: <count> · Sources: <count> · Verifications: <count>
Research usage: workers <observed>/<target> · queries <observed-or-unknown>/<target> · waves <observed>/<target> · provenance <handoff|journal|self-reported>
Retrieval integrity: ok <n> · partial <n> · blocked <n> · empty <n> · quota <spent-or-unknown> · re-dispatched lanes <n>

## Executive answer        — 2-3 paragraphs answering the core question, valid as of <date>
## Findings by theme       — per theme: consensus, evidence links, key quote (<20 words, attributed), verified yes/no
## Codebase findings       — absolute or repo-relative paths with line references
## Sources (ranked)        — URL, what it contains, grade, retrieval verdict, observed date, as-of date
## Verified claims         — code: claim | verdict | verify-<slug>.md · non-code: only rows cleared into verified-claims
## Contradictions          — source A vs source B, which surfaces they sit on, resolution with evidence
## Gaps                    — what saturation could not answer · unresolved/refuted claim-ledger rows · blocked sources with no substitute · deferred claims and why
## Expansion trace         — per wave: workers → markers; retrieval verdict mix; convergence reason
```

Deliver the synthesis with inline `[Source N]` citations on every substantive claim. In `## Sources`, define each numbered source on its own bullet as `- Source N: <locator> ...`; prose elsewhere never defines a source. In `## Verified claims`, put every claim on a structured row `- <claim-id> | <verdict> | <artifact-or-ledger>` so the validator can reject uncleared ledger ids and require every non-ledger id to name a present `verify-<slug>.md` artifact. Every high-risk non-code claim you assert must be a verified-claims row from Phase 3b — assert nothing left in the unresolved/refuted annex. Keep direct quotes short and attributed; do not copy long passages. When no report was requested, this is the deliverable.

## Phase 5 - Report (only when requested)

Format by the user's words: "report"/"document" → markdown (default) · "pdf" → HTML first, then a renderer · "slides"/"presentation"/"deck" → a slide builder · "html"/"webpage" → standalone HTML.

Asset workers (parallel): charts for quantitative findings, full-page screenshots of the top 5-10 sources, and generated diagrams when architecture or flows need them — saved by you under `<evidence-root>/assets/`.

Assembly: before writing, load every available design and visualization skill and apply it — the report is a designed artifact, not a text dump. Structure: executive summary → key findings by theme → detailed analysis (quotes under 20 words with attribution, charts, SHA-pinned permalinks, verification results) → comparative analysis when options compete → numbered sources with access dates → methodology appendix (workers, waves, searches, verifications). Every claim cites `[Source N]`. The orchestrator owns this write: assemble it yourself, or have a writing lane draft content returned as message text and write it under the evidence root — a designated writing worker that produces the file ends its reply with `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.

Close the research with `superloopy loop evidence --status pass --artifact <report-or-synthesis>` pointing at the deliverable. Note: `superloopy loop report` is a *separate* command that generates a complementary evidence-trace summary (evidence root, ledger, progress) to its own path — it is not a publisher for this designed report, so never point it at your report file or it will overwrite your content. Run it, if at all, against a distinct path such as `<evidence-root>/evidence-report.md`.
