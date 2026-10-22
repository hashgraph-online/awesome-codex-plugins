# Optional rendered-page review and bounded text repair

Candidate version 1.5.0-rc.4 supports an explicitly selected vision model through
Codex or an OpenAI-compatible endpoint, including a running local server.
Production translation and visual repair models are configured independently;
see [production workflow](production-pipeline.md). No automatic model upgrade,
new login, model download, model tools or persistent permission change occurs.
Document images/text and model replies are untrusted data.

`provider.vision: true` is mandatory. Before any document image is submitted,
the same endpoint/model must read a random code that exists only in image pixels.
Failure stops the run; there is no text-only inspection or premium fallback.
This checks image transport/capability, not translation quality. Every run spends
one fresh probe call, including a cached replay, so changed model aliases are checked.

Copy `assets/visual-review.example.json` beside the PDFs. Set the actual model,
physical page numbers and fresh output folder. The two inputs must have matching
page counts, dimensions and rotation. Relative paths resolve against the job.

```sh
python scripts/visual_review.py review.json
python scripts/visual_review.py review.json --execute
```

The first command validates a dry run, without model calls. Start with high-risk
pages and `repair: false`. With `repair: true`, the program may replace eligible
plain text blocks and must render/review the candidate before accepting it.

The model sees two page images, up to three aligned detail pairs, and source/target
prose metadata (math transcription is excluded), then returns
typed issues: translation, structured output, segmentation, layout, formula,
table, figure text, header/footer or missing translation. It may identify only
program-generated block IDs. Model-proposed coordinates and arbitrary fields
are rejected. A graphical or unmappable issue uses an empty block ID.

Automatic repair has two conservative paths:

- Replace a whole horizontal, uniformly styled text block only; no new numbers,
  changed numeric values, formula operators, placeholders or omission notices.
- For mixed text/math, table headers or segmentation failures, derive a closed
  island from intersecting source and target text blocks. Maximum height is the
  smaller of 280pt and 36% of the page; width is at most 92%. Reject images,
  rotated text, changed vector drawings, oversized closures and unknown regions.
  There are no paper-specific coordinates or translation overrides.
  An empty formula finding can be mapped only when its reason explicitly names
  a unique printed equation label and a bounded following prose boundary exists.
  That mapping is recorded separately; ambiguous/unmapped findings remain manual.
  Closure uses rendered ink bounds to avoid pulling in neighboring font margins.
- Restore the original source island on a scratch page. Known math fonts
  (CM/MSAM/MSBM/STIX/Math/Symbol), explicit math glyph spans, monospace contact
  identifiers, equation labels and compact table IDs remain original PDF objects.
  The page reviewer sees the images; the repair subrequest receives numbered
  prose gaps, their paragraph IDs, neighboring immutable literals and capacities.
  Source math, contact identifiers, equation labels, compact table IDs and name
  suffixes attached to source math remain program-owned.
  Source/target crops are retained as audit evidence, not attached to this text
  subrequest. Each source paragraph must remain nonempty; Chinese words and
  prose numbers may move among its gaps for correct grammar. Numeric counts,
  bracketed units and alphanumeric IDs must remain exact within that paragraph.
  Content cannot move into another paragraph, and new math/ellipsis placeholders
  are refused. Literal guards do not prove that every qualifier was translated.
  It cannot return coordinates or regenerate formulas.
- Flow Chinese through the original prose gaps. Verify unchanged protected
  font/text/origin signatures and 144dpi protected pixels, including new ink
  overlapping an original formula. Ineligible or unfit regions retain the
  previous output and record a reason. Unknown font conventions and dense
  interleaved mathematics can still require engine or manual work.
- Escape text before HTML typesetting; mixed Latin/CJK uses normal font fallback.
  Reject replacements that require shrinking below 85% of the original size.
- Check page count/size and every page's pixels at 96 dpi outside the edit boxes
  (three-pixel antialiasing margin). The follow-up model review must reduce the
  weighted issue score inside the modified regions and introduce no new serious
  category there. New serious findings with unknown location also veto acceptance.
  Previously reported outside findings remain unresolved; newly noticed defects
  on unchanged outside pixels are retained as well. They cannot be claimed fixed
  by a local edit, and the document stays `needs_manual_review`. Raw before/after
  reviews and the local acceptance decision are kept. Otherwise retain the previous
  PDF. These guards do not prove semantic correctness.

Optional `focused_recheck: true` replaces the global follow-up with a source /
before / candidate comparison for every program-owned edit island. Vertically
stacked images preserve small-type resolution. Actual source/candidate prose slots
are supplied as an additional semantic trace; extracted formula transcription is
not used as proof of visible mathematics. The model reports new/worse defects
explicitly, including a newly lost concept in an existing issue category. Every
edited island must improve independently, with no new/worse finding; an improved
neighbor cannot offset a regression. All outside or unmapped original findings
remain unresolved. On rejection, the second allowed round starts from the retained
PDF with rejection feedback, never from a rejected candidate's block IDs.

Optional `preserve_contact_metadata: true` requires an operator policy to retain
original names, institutions, contacts and URLs. It restores complete source
contact blocks, including short connecting words, instead of translating fragments
between emails. This may legitimately have zero prose slots and needs no prose
planning call. Other prose in the island is still translated. It is not a general
permission to leave ordinary paragraphs untranslated.

Optional `preserve_tiny_connectors: true` retains an original short English
connector only between two immutable objects in one source paragraph when its
prose gap has capacity below one CJK character at the 85% font floor. For example,
original `in` between a symbol and its equation reference remains at its exact
source coordinates. It cannot become a missing relation or a moved equation
reference. The report lists each retained word and its reason; other prose is
translated. This explicit fallback prioritizes mathematical meaning over an
all-Chinese appearance and is disabled by default. Formula/glyph/pixel guards
remain unchanged.

Protected source text is checked per **visible glyph**, font, size and original
origin. Removing an adjacent blank may split a PDF text span; the visible math
glyph's own origin must remain exact. Pixel/collision checks still apply. A
space-only span boundary change cannot excuse a changed mathematical glyph.
When only a font's blank ascent/descent margin crosses an island edge, a clipped
288dpi ink check scopes the signature to glyphs actually affected there. A
descender or accent with visible ink inside remains protected, even if its origin
is outside. Full-page pixel checks still reject visible changes outside the island;
this is not permission to drop neighboring mathematics.

Optional `math_operator_guard: true` audits supported delimited inline
`max/min/sin/log` calls using source math-font argument evidence. It compares
complete operator/argument signatures; prose words such as "maximum", "min speed"
and "log files" are not calls. Unknown/unclosed arguments are not a pass.
Missing/changed calls generate critical findings, mapped only through unique
printed equation labels and bounded source regions. Original operator glyphs
stay immutable during source-prose repair. A recovered exact call can establish
objective improvement only with successful source-object/pixel verification and
a nonworsening focused image response; local operator regressions veto acceptance.
This is a limited audit, not proof of all formulas or semantics.

Optional `chinese_prose_guard: true` is explicitly for an English-to-Chinese
mono target. The production pipeline enables it for an explicit Chinese target;
standalone review can opt in. It conservatively flags an unchanged ordinary English sentence
that occurs uniquely in the source page. It excludes CJK/bilingual prose,
short labels,code,contact/URL data,title-style names and strong bibliography
evidence. The source comparison is read-only; no language or mathematical
content is rewritten by the screen. Initial and retained-final checks keep
such a finding unresolved even when a blind image model returns no findings.
It does not detect every untranslated fragment or prove meaning equivalence;
relation/qualifier errors still need source-grounded semantic review.

Optional production `review_mode: "math_audits"` starts from the enabled program
math audits instead of a whole-page model request. It requires `focused_recheck`
and at least one math guard. Only findings derived by those audits may authorize
repair; every edited island still needs source-object/pixel checks and a focused
source/before/candidate model comparison. A fresh capability probe remains
mandatory. This can avoid replacing an already correct mixed-math paragraph
when the engine has fixed it and only a different definition needs repair.
It does not check the rest of the page for meaning, figures, tables or layout.
Successful limited work is labeled `targeted_repairs_screened`, or
`program_math_audits_passed` if no edit was needed, never `model_screened`.
The CLI retains exit code 2 for these limited outcomes, as for a sample review;
inspect the report status. Whole-page/independent acceptance remains a separate
step. This mode cannot serve as `development_acceptance`.

Optional `math_scale_guard: true` adds a deterministic risk check before repair
and after each candidate. Unique, unmoved printed equation labels and the same
bounded source-island logic identify nearby definitions. Matching math-font /
character counts provide size samples; at least eight samples and 60% coverage
of both islands are required. A median below 85% of source size remains a major
formula risk even if the page model missed it. Matching sizes do not prove
formula equality. Unknown fonts, moved/ambiguous anchors and insufficient matches
are reported as `not_checked`, never as checked/passed. Local risks in the candidate
veto acceptance; risks outside an edit remain unresolved. This check has no paper
coordinates and does not change the source mathematics. The actual Luna high
page5 review missed a 75% matrix-definition scale, which motivated this guard.
When the model reports no issue in either image, an island may improve only by
separate program evidence: a prior measured risk, successful source-object/pixel
restoration, exact math-font/character counts and a checked fixed-island scale
above the floor. The model must still report no new/worse defect and its issue
score and serious category counts must not increase. Unknown measurements cannot
establish an improvement. Every edited island needs its own evidence; unrelated
or unmapped findings remain unresolved.

Critical and major issues precede minor issues. While any serious issue remains,
the loop does not spend a repair call on a cosmetic edit. The report records
source-island refusals. An unmappable finding cannot authorize a page-wide edit.
Extracted `(cid:N)` text is not evidence of a rendered formula defect; the reviewer
is explicitly required to check the image. Cosmetic alignment/wrapping is minor;
meaning loss, unreadable text, overlap and cropping remain blockers.

Limits are hard caps on provider **attempts**, rounds (maximum two), per-page edits
and elapsed model-call time. Failed/uncertain attempts count too, with zero
automatic retries. The capability probe consumes one attempt. A page is not edited without remaining follow-up-call budget.
There is at most one explicit source-plan correction after local schema/fidelity
rejection, using the same model. Both replies and attempt usage are retained;
a second rejection stops without changing the retained PDF. This is separate
from transport retries, which remain disabled.
Source-prose planning consumes one extra call and reserves the follow-up before
requesting a plan. Its verified cache can be replayed. The per-page edit cap
applies across both rounds, including rejected candidates, rather than resetting
for each round.
Fit failures can use the same single correction opportunity as fidelity failures.
The program also tries prose scales 100/95/90/85% and 0/0.6/1.2pt leading shifts
locally, retaining the original
math size and accepting only a variant whose protected glyphs/pixels pass.
The time cap cannot bound PDF rendering/saving time or revoke already consumed
tokens. There is no authoritative per-call monetary quote for the configured route;
`cost_usd` stays null, never zero. Native input/cache/output counters are recorded
with their provider names and are not summed as disjoint quantities. Choose a
small `max_model_calls` as the spending boundary. This workflow cannot guarantee
a hard dollar cap; use an independently priced/budgeted route if that is required.
Native CLI calls can reconnect internally; backend transport attempts are unknown.
Each visual/planning invocation has a metadata-only start/return journal. An
interrupted start record is an uncertain call with unknown usage; it is not
silently omitted from cost accounting. A fresh capability probe still costs one
call on cache repeat. Low-reasoning Luna screening has produced false negatives
on dense mathematics, so a screening result cannot replace independent acceptance.

Standalone review accepts optional `translation_context` (at most 32000 characters)
for the operator's prompt and glossary. The production pipeline snapshots the
translation job's actual prompt and glossaries and supplies them to review and
source-prose planning; a change during translation fails before visual requests.
Term preferences cannot override schema, formula preservation or fit guards.
The bounded source-prose fitter in this candidate is validated for English-to-Chinese.

Keep caches and review folders private: they contain document text/images and
structured findings. Cache identity covers model, reasoning effort, native CLI
version, API endpoint/format, prompt/schema and both image hashes; verified page-cache
hits spend no new review calls, but the fresh capability probe still spends one.
Windows uses inherited directory ACLs; POSIX also enforces mode bits.
No permission is broadened. Inputs and rejected candidates are retained.

`best.mono.pdf` and `best.dual.pdf` are the best retained candidate, including on
failure. `review-report.json` distinguishes `model_screened`, sampled screening,
`needs_manual_review`, `budget_exhausted` and `failed`. Only all selected pages
without reported issues receive the screening status; unscreened pages are never
counted as checked. Exit 2 includes unresolved/sample cases. A screening result
is not a human acceptance certificate or proof that the formula content is right.

The R1 region script in `scripts/repair_r1_regions.py` remains a separate,
source-hash-pinned paper-specific supplement, not a generic repair backend.

The ordinary example selects Luna explicitly. `visual-review.development.example.json`
selects Astra with `purpose: development_acceptance` and `repair: false`; that
role rejects repair=true. It screens the final production result independently.
It never substitutes for the production model's own review/repair/recheck loop.

For prose adjacent to math, optional `engine_job` selects the completed original
translation job as a cache-only rerender backend. Set `engine` to the same local
BabelDOC executable when it is not on PATH. The original job must retain its
complete `translation_pairs_file` and native cache. This backend requires full-page
review (`focused_recheck: false`, `strict_repair_objects: false`).

Native source gaps are uniquely linked back to complete original engine paragraphs.
All style and math markers stay in their original order. Unmatched source groups
are recorded and retained. A separate meaning check can veto the proposed text;
only then is a separately bound correction receipt applied after the immutable
base cache. The native engine is forced to `cache_only: true` and creates fresh
outputs, diagnostics and pair receipts. It cannot silently start new translation
calls. Pair receipts must prove unchanged source/base and exactly the selected
replacements. Other pages' pixels must remain identical.

This backend discloses whole-page reflow and reserves calls for both meaning
screening and the mandatory rendered full-page follow-up. It does not require
new Chinese prose to fit the old English gaps. It preserves all content guards;
ambiguous matching, semantic uncertainty, failed cache lookup, receipt mismatch
or visual regression keeps the previous PDF. The usual round, call, region and
time limits still apply. This is model screening, not a validated semantic proof.
