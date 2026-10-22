# Optional bounded semantic and PDF quality pipeline

The complete source/target paragraph screen is separate from literal marker
fidelity and PDF image review. An opt-in rc.5 orchestration now connects all
stages under one persisted call budget. The
[second live round](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10) exercised
the path but still missed a known semantic role error, so acceptance remains
failed. The [first-round evidence](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10)
is also retained. A model screen is not independent acceptance.

Copy `assets/semantic-pipeline.example.json` outside the skill, point its
`translation_job` to an English-to-Chinese Codex/DSH native job with
`provider.output_contract: "paragraphs"`, select pages and explicit call/time
limits, then plan and execute:

```text
python scripts/pdf_pipeline.py semantic-pipeline.json --engine babeldoc
python scripts/pdf_pipeline.py semantic-pipeline.json --engine babeldoc --execute
```

`scripts/semantic_pipeline.py` accepts the same arguments directly. Planning
makes no model call. Output must be fresh. The template's24 calls are an
example budget, not authorization to spend it; select the intended limit.
`review_mode: "math_audits"` is required for this profile. Program math findings
drive guarded source-prose repair; meaning findings drive native rerendering.
Final visual requests include whole source/before/candidate pages plus detailed
repair islands. No Astra fallback, account or credential is selected implicitly.

An explicit native-provider `translation_pairs_file` records complete actual
source/target text, including cache hits and post-correction output. It needs
a fresh private file and completed footer. It contains document text, so keep
it private. `semantic_review.load_translation_pairs` rejects incomplete or
duplicate records. Collections are limited to4096 pairs/32MiB, automatically
and completely batched into at most64 pairs/200KB per request. Truncation is
forbidden; larger inputs fail visibly.

`schema`, `prompt` and `checked` implement a complete named-pair screen with
equivalent/different/uncertain statuses and exact contiguous quoted evidence.
Opaque math identities are local to each paragraph. They may move as whole
objects for Chinese grammar; names or formulas must not be invented or
expanded. `screening_status` returns `needs_manual_review` for a discrepancy
or uncertainty, including after a clean visual response.

`repair_schema`, `repair_prompt` and `checked_replacements` create whole
paragraph candidates only for program-selected findings. Existing marker,
style, number and configured-name protections remain mandatory. A separate
`quality_corrections_file` binds the real request, immutable base response,
source rows, previous targets and actual correction/recheck response hashes;
it never rewrites a native cache. Current receipts support batch paragraphs,
not arbitrary single-string repair or unbounded correction stacking.

After an actual verified source-prose restoration, use its `semantic_pair`
and `reflect_source_restorations` to replace only a uniquely matching raw
paragraph with its actual prose/opaque-object template. Ambiguous links fail.
PDF content changed by another repair method needs its own verified complete
mapping; auditing stale native text is not final acceptance.

`region_review.prose_review_island` derives a bounded read-only crop from
unique complete source prose and all three pages' real text geometry. It
records drawing/image geometry differences for review. It cannot authorize
source copying, redaction or model coordinates. Source-object repair uses
the stricter unchanged-graphics/pixel guards in `source_repair` as before.

A caller must persist one shared hard invocation budget, count failed or
uncertain calls, set maximum rounds/corrected rows, record selected models
and actual native usage, and stop visibly at the cap. A model screen never
proves correctness; final PDF math audits, outside-region regressions and
rendered review remain separate vetoes. Known defects cannot be waived to
manufacture an accepted freeze. No additional credential or fallback model
is selected by these helpers.

The pipeline performs initial guarded math repair, complete semantic detection,
one grouped correction round of at most8 source-linked paragraphs, and a
complete precheck. Only a validated clear screen creates a separate correction
receipt. Actual rerendering is cache-only: an unexpected miss fails before
inference. New actual rows are linked by request hash and type-sensitive row ID,
with source/base/output hashes checked; pair enumeration may legitimately change.
Source/base changes, missing/extra origins and unexpected targets fail.

Mathematical repair is reapplied and actual source-prose templates replace only
uniquely linked stale raw rows. All final actual pairs must equal the reviewed
candidate after that mapping. Source-derived QA regions are read-only; every
outside pixel on every page must remain identical. Every repair island needs
an improved image response and no new/worse finding. Unmapped whole-page issues
remain unresolved even if forgotten by the after response. A final complete
semantic gate and conservative unchanged-English guard can still veto success.

`semantic.fresh_final: true` requests another native final check for every batch.
Explicit `false` permits a semantic cache hit only for the exact final actual
texts, schema, model, native version and provider identity. That cache use is
recorded separately and is not a fresh final judgment or cold-start evidence.
The live canary runs once per verified model/session, shared by all stages.
All translation retries, semantic checks and image calls use the same hard
`max_model_calls` and wall-clock limit; unknown usage remains unknown.

The current workflow starts from an uncorrected native base; correction receipt
stacking is unsupported. A discrepancy in an already source-restored paragraph
stops visibly instead of applying incompatible native opaque markers. Ambiguous
source evidence, oversized regions, unsupported scans, excessive findings and
unmapped graphical defects require manual review. Source objects retain the
existing graphics/glyph/pixel guards.

Keep generated text receipts and native outputs private. The output includes
the shared ledger, source/restoration and rerender associations, actual model
responses, full-page/detail PNGs, final complete pairs and per-region decisions.
`sample_model_screened` covers only the selected translated physical pages;
it does not make a one-page translation in a21-page container a full paper.
Run independent representative/full cold validation before promoting a candidate.

## Offline mechanism update and quality states

The [offline audit](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10)
corrects the original9-pair comparison: faithful and wrong alternatives to the
same sources shared a context, so its3/3 detection was not independent blind
accuracy evidence. New complementary control packets reject same-source answer
alternatives and keep evaluation labels out of model input.

Reports now separate `execution_status`, `model_screen_status`, `quality_status`
and `quality_passed`. Known failed source/target/document hashes in explicit
`semantic.regression_corpora` veto promotion; they never supply an approved
replacement or a blind-model answer. Unknown/uncertain results, missing full-page
checks, absent relation witnesses and an unvalidated protocol stay blocked.
Requested pages with no text correction still receive full-page image review.

`semantic.protocol: "summary-v1"` is retained for legacy comparison; empty
finding summaries do not establish relation coverage. Experimental
`"relations-v2"` requires unique verbatim quotes, subject/predicate/object anchors,
modifier/reference/quantifier/condition witnesses, consistent conclusions and
complete lexical quote coverage. It uses a different prompt/schema and cache
version; legacy equivalent replies cannot serve as these witnesses. This is an
offline-tested proposal. The [authorized isolated pilot](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10)
stopped after one of two allowed calls:12 raw labels matched the controls, but
two pairs failed role evidence and one had quote-coverage gaps. The second arm
was not run. No rule was relaxed after seeing the result. Lexical coverage cannot
prove semantic truth; this protocol remains unvalidated and `quality_passed`
remains false. Any revised experiment needs a separate explicit budget.

An offline-only [literal-span proposal](relation-span-contract.md), protocol
`relations-spans-v3` / contract SemVer `3.0.0-draft.1`, adds ordered exact
coordinate spans and explicit intervening attachments. It does not change the
failed v2 experiment or production protocol selection. Old replies are lifted
only when already verbatim; no missing role is reconstructed. New authored
controls also demonstrate semantic errors that remain literally admissible, so
known-regression and unvalidated-protocol vetoes stay required.

The [output-stage audit](final-audit.md) is separate from `semantic.fresh_final`.
Even when semantic caching is allowed, terminal image requests read actual final
PDFs/source in fresh contexts. They cannot clear known-D02 or validate a relation
protocol. Both pipelines use the same delivery gate.
