# Windows/R1 bounded prerelease: rc.28

Current source: `fba043bdc6a6d33bc889ac1459171dd18876821f` (merged PR #14). Engine overlay: `0.6.4-pdftranslate.math-integrity.3`. This prerelease covers the recorded Windows Luna/BabelDOC workflow and R1 reading preview; it is not full-paper cold-start or general automatic-repair acceptance.

Windows offline results are 622 passed / 2 skipped; Linux CI is 594 passed / 30 skipped (29 unavailable real-document evidence checks and one Windows-only check). Independent rc.28 checks passed 14 offline tests, 15 configuration comparisons and 271 fixed-source file comparisons. The six-file runtime patch and 83 skill mirrors passed their recorded checks. See the [complete current report](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10#issuecomment-6251690944) for immutable run links and artifact identities.

The R1 page 3 overlap is fixed. Two 11-page cache renders each used 66 hits and zero new calls/failures; text, size and 144 dpi pixels matched. Other ten pages were unchanged by the layout fix. Minor English coverage/preservation, terminology, footer association and wrapping issues remain. PyMuPDF 1.28.2 can omit an equals sign in the bilingual 600 dpi view; lower-resolution views, the mono output and PDFium 600 dpi were normal. This exception prevents a blanket pixel-equality claim.

L1Quad (arXiv:2302.07208) page 5 failed its real empty-cache pilot after five Luna/low calls: a missing math placeholder followed by invalid slots caused `INVALID_TEXT_SLOTS` / `BRIDGE_ABORTED`. No PDF was produced and no cache rerun occurred. Its full-paper acceptance remains incomplete. Source pass-through diagnostics are untranslated.

rc.28 accepts explicit Codex `max` settings and passes mock argument-forwarding checks. Real `max` inference and full Astra final review remain unverified. Luna is the production translator with a separately configured economical vision/repair role; Astra is development-only. `PROTOCOL_VALIDATED=False` is unchanged.

The chronology below preserves earlier observations. Historical draft/pending wording is scoped to its named version and does not supersede the current status above.

# Historical engineering sequence

This draft carries the Windows work through rc.24 into a clean branch based on
public main, then fixes the review-context treatment of the original translation
contract in rc.25, corrects paragraph/formula bounds in rc.26, and fixes native
borrowed-view lifetimes and test portability in rc.27. It contains implementation and tests, not a claim of completed
full-paper quality acceptance. No production protocol flag is enabled.

## Changes that are ready for code review

- Named structured rows and text slots retain original PDF markers, reject empty
  or merged rows, and keep bounded retry and native-call accounting.
- Source-literal, date, name-fragment and paired-tag checks reject changes while
  retaining correct legacy caches after revalidation. Hidden formula contents
  are not guessed from their placeholders.
- Windows process containment and diagnosis distinguish execution identity,
  unavailable authentication and timeout; no credentials or account settings
  are read or changed by the repair logic.
- Optional visual/semantic pipelines bind source and candidate artifacts, use
  explicit models and budgets, retain rejected candidates, and recheck actual
  rendered pages. Durable receipt and coverage checks keep their known limits.
- rc.25 validates the translation contract before serializing review context.
  Explicit preservation requirements are required scope, rather than being
  labelled "terminology/style only". Math, schema and source-binding guards
  remain authoritative. This prompt correction is not proof a model will obey it.

## Observed results and remaining acceptance

The fixed rc.24 Windows candidate passed 607 of 609 offline tests, with two
existing platform skips. R1 recovery produced both 11-page output variants.
Two complete cache repeats each used 66 cache hits, zero new calls and zero
failures; all pages in both variants had equal text, dimensions and 144 dpi
pixels. Only page 7 changed after the paired-tag fix. Successful whole-paper
runs resumed verified checkpoints; a successful complete empty-cache run has
not been established.

The last bounded stage used nine additional Luna translation calls, reaching
89 of 96. Luna/high review and repair used 21 of 32 calls, with one timeout whose
token usage is unknown. No repair from that stage passed recheck. A separate
independent review covered all 11 pages without new API/native calls. It is a
rendered-document review, not the separate Astra final audit.
Call counts and unknown cost are reported separately from repeatability.

That review identified one release blocker in rc.24: translated prose on page 3
starts inside the visible inline formula ending `= x`. Source geometry shows that
synthetic spaces remain after adjacent mathematical glyphs are grouped; those
spaces pull the prose paragraph's left boundary into the preserved formula.
rc.26 corrects the horizontal bounds of only the paragraphs that donated math
glyphs, retaining source objects and vertical metrics. Two fresh full renders
each used 66 cache hits and zero new calls or failures, with equal text,
dimensions and 144 dpi pixels. Both variants changed only the affected page 3
region; the other ten pages remain equal to rc.24. The checked formula crop matches the original; the later bilingual MuPDF
600 dpi exception is documented in the current status above. The fixed rc.26 source passed 620 of 622 local
tests with two existing platform skips. The later independent recheck is summarized above.
Inspection crop coordinates are evidence only, never repair coordinates.

Linux CI exposed two native lifetime errors: an owning path wrapper dropped a
borrowed callback path, and a temporary matrix released the owner of an
`internal()` view before low-level queries used it. rc.26 fixed the former;
rc.27 retains the matrix owner through both queries. Child-process replay checks
actual fill classification and clipping/render stability. An owner-expiring-view
counterexample fails on rc.26 and passes with the fix. Offline adapter tests also
stub executable discovery and give synthetic legacy cache files the private
permissions required on POSIX. All 99 targeted local tests pass; The later complete Linux CI result is summarized above. Bounds, fidelity and budget guards are unchanged.

All 105 Table 2 values and their row/column positions were consistent. The other
observations below were classified as minor disclosed limitations under the
user's reading-preview criteria; their raw findings remain available locally:

| Observation | Engineering implication |
| --- | --- |
| Volume/date/footer fields kept their digits but changed their association | Opaque formula groups can contain multiple metadata fields. Do not infer a hidden day/volume or reorder them by keyword. Prefer a source-bound minimal correction after the actual fields are inspected. |
| A benchmark `-shot` suffix became a word meaning shooting | This is a minor terminology error; numeric guards alone cannot establish technical terminology fidelity. |
| Parts of references and affiliations were translated despite an English-preservation instruction | Review must carry the original preservation contract as required scope. The existing partial translations remain disclosed; the contract has not been silently changed. |
| A complete `<think>` opening tag wraps across two lines | A readable wrap with all letters and punctuation intact is a minor layout limitation, not automatically a semantic or mathematical failure. Raw model severity is retained separately from the controller assessment. |
| Figure text remains English inside preserved original raster images | Disclose the retained original figure content. This draft does not add a general OCR/figure translation subsystem. |
| A sentence spans two columns | Review both fragments together; do not call a quantifier missing when it appears in the other column. |

The earlier L1Quad D02 false-negative and other negative controls remain in the
test fixtures. `PROTOCOL_VALIDATED` remains false. A model clear verdict, matching
literal inventory or successful render does not independently certify semantic
equivalence. Minor imperfections can be accepted under the user's criteria;
the independent page review does not replace the pending development final audit
or the new-paper acceptance run. No contract is silently shrunk here.

The satisfied historical Stein output used ten targeted prose revisions plus
a paper-specific source-vector reinsertion. That history motivated bounded
review but is not represented as a general algorithm. Existing R1 coordinate
utilities are likewise explicit paper-specific tools, not automatic repairs.

## Reproduction and distribution

Use the pinned dependencies and runtime patch checks in `tests/README.md` and
the CI workflow. The default suite runs public synthetic/small attributed
fixtures. Large geometry extracts, full PDFs and raw response archives are
external optional evidence: set `BABELDOC_EXTRA_TEST_DATA` to a separately
verified evidence root to enable the related tests. Missing evidence is reported
as a skip, never as a passed real-document check. The existing coverage corpus
and actual-slot pilot also remain explicitly opt-in.

This branch excludes private candidate Git history, full-paper PDFs, page image
archives, native event logs, personal paths, credentials and virtual environments.
The implementation is available for review while acceptance is pending.

Tracking: [issue10](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10),
[rc.24 result](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10#issuecomment-6250638333),
[minor-layout clarification](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10#issuecomment-6250690617).
