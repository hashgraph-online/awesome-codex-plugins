# Output-stage audit

The normal chain remains: economical translation -> BabelDOC -> economical
vision review -> targeted repair -> recheck -> independent final context ->
delivery gate. Luna and existing compatible/local vision endpoints remain
explicit choices. Astra is restricted to separate development acceptance;
it cannot translate, review/repair production output or clear delivery.

This isolated development version is `1.5.0-rc.15`. The audit implementation is
`scripts/final_audit.py`, contract `1.0.0-draft.6`. It is not validated for real
production quality. `PROTOCOL_VALIDATED` remains false; config files and model
replies cannot turn it on. Known D02 and previous failed controls remain vetoes.

## Invocation and scope

Use the existing pipeline job and add an explicit audit config:

```text
python scripts/pdf_pipeline.py pipeline.json --final-audit-config assets/final-audit.example.json
python scripts/semantic_pipeline.py semantic-pipeline.json --final-audit-config assets/final-audit.example.json
```

These are dry runs. A separately authorized real run adds `--execute`. This
offline development request did not authorize or execute any model run.
No credential, model upgrade or installation is performed by the audit layer.
Copy/edit the example outside the package for a real job.

The terminal layer freshly reads the source and actual final mono/side-by-side
bilingual PDFs after upstream recheck. It checks page counts and geometry,
renders all final physical pages, and attaches source/mono/dual images plus
freshly extracted text metadata. Metadata assists reading; formula glyphs must
be examined in images. The configured translation-page scope is explicit, so
intentional source-language pages are not mislabeled untranslated. All final
pages still receive composition/layout/object review.

`translation_pages` comes from the original job, independently of upstream
`review_pages` sampling. `selected_pages` retains the translation scope in
pipeline reports. Full translation with sampled review still requires the
target language on every requested page; translating only p5 still audits
layout on all retained container pages. Both entry points snapshot the prompt,
parsed glossaries, original file hashes, source/target language and requested
pages as a sealed contract. It reaches every fresh audit and actual terminal
repair/recheck, without earlier findings or pass decisions. A changed contract
invalidates the receipt. Delivery verification requires a fresh expected
contract, not a value copied from an old receipt. The current terminal layer
explicitly supports English to Simplified Chinese only; standard hooks reject
other language jobs before translation.
Visual review records this requested scope separately too. Pages intentionally
retained in the source language are inspected for layout, skip the Chinese
omission screen, and cannot be automatically translated by either repair path.

Each audit request uses a fresh native process or stateless compatible request,
with no previous findings, approvals, corrections or result-cache entries.
The prompt covers omission, substantive semantic/math relationships, formula
objects, tables/figures, headers, columns, clipping and repair regressions.
Output is `clear/defects/uncertain` and observed issues. The model supplies no
replacement or coordinates. Same-model errors can remain correlated despite
fresh contexts; this is not statistical model independence.

## Bounded repair and evidence

The default is one additional terminal repair round; the hard maximum is two.
Every terminal probe, page audit, repair/recheck and complete re-audit shares
one terminal call/time budget. A complete next audit is reserved before edits.
The normal translation/review budgets remain separate unchanged caps; the
terminal budget does not claim to be a single total-job monetary limit.

One image capability probe plus one request per final page plus one request
per complete semantic unit in the translation scope is the initial minimum.
The 12-call example is only a cap, not a promise to cover any document. The
complete initial request count is checked before inference; larger jobs
need an explicitly reviewed limit. All exceptions/unknowns stop without an
automatic retry. Usage/model and unknown monetary cost are recorded; internal
HTTP attempts may be unknown.

## Complete-block semantic screen and v3 receipts

`semantic_mapping.py` reads unfiltered actual source/mono text, including math
fonts. It builds source/target overlap components generically, with no paper
coordinates, named defect selection or expected answers. Every extracted block
in scope must belong to exactly one complete unit. This is a conservative
correspondence candidate, not a proof that geometry determines meaning. A
component can contain several complete blocks; it is never silently truncated.
Unmapped/empty/oversized units, extraction replacement glyphs, duplicate text,
unextracted images, unchanged English prose and changed protected math/number
inventories veto coverage before any model invocation. Image content is not
automatically OCRed. Legitimate reflow or intentionally retained bibliography
can therefore require manual mapping; there is no automatic waiver.

For each complete prose unit, `semantic_gate.py` sends a separate fresh native
request with the full source/target text and original translation contract.
The explicit economical semantic provider must have zero wrapper retries; no
cache or automatic model upgrade is used. The four-field response contains a
verdict and short factual source/target statements. `different` or `uncertain`
vetoes the candidate even when the page image audit says clear. This layer does
not turn model statements into replacements or automatic semantic repairs.
The prior bounded visual/plain-prose repair adapter and mathematical contracts
remain unchanged; new semantic vetoes require manual/engine correction.

Equivalence additionally requires an independent trusted statement adjudicator
to publish a matching `decision.ready` in the unit's v3 inbox. The built-in
`file_adjudicator` only waits up to the configured 0–90 seconds within the shared
deadline; elapsed time never counts as approval. It does not invent factual
support or call another model. The controller must independently check the full
texts and factual statements, then publish the v3 receipt with the exact binding.
The checker is `audit_receipts.py` core `0.1.0-draft.2`, reused from receipt-v3;
the semantic response protocol remains `0.1.0-draft.1`. No historical unsigned
case is reconstructed. Directory ownership is trusted; hashes do not authenticate
the reviewer's identity or establish semantic truth.

Before parsing, the private audit folder retains exact answer bytes, lengths,
SHA256, request, reservation and source/target/artifact bindings. Native event
stdout is retained as decoded UTF-8 with explicit size/capture metadata; native
stderr is hash/size only. Internal HTTP attempts and currency cost remain unknown
when the provider does not expose them. These folders contain document text and
must not be published as public diagnostics without review.

Signing interruption recovery is an explicit Python API
`semantic_gate.run(..., resume=True)` against the same folder, same complete
coverage and same PDF/contract hashes. It may sign already durable raw answers
without inference. It cannot invoke missing/unknown calls, extend the original
deadline, clear terminal blocks or restart the full final-audit pipeline. A new
controller must handle that limited recovery deliberately. A full automatic
pipeline resume is not implemented. Delivery re-extracts coverage and rechecks
every expected unit, raw response, binding, v3 receipt and event hash against the
actual final PDFs. The optional semantic config is required to pass delivery;
omitting it only permits a blocked visual diagnostic.

Twelve independently reviewed standalone semantic controls justified this
integration experiment. They did not validate automatic full-page mapping, this
new combined prompt, a real whole-page run, mathematical equivalence, production
delivery, cold-start translation or cache stability. The hard
`PROTOCOL_VALIDATED=False` and known-regression veto remain active.

Defects return to the existing visual repair/recheck adapter. Only exact
program-owned region IDs can define permitted islands. Unmapped graphics,
ambiguous locations, unaddressed findings or source/object failures require
engine/manual work. Repairs write new mono/dual files; previous artifacts must
remain unchanged. Fresh program validation checks outside-island pixels,
geometry, math operators/objects, conservative omission screening and actual
bilingual composition. Every finding must be accounted for before a new final
context audits the revised artifacts. An issue disappearing from the next
reply is not, by itself, evidence of a repair.

The terminal adapter uses one source-derived editing contract in preflight,
actual candidate acceptance and independent revalidation. A typed text grammar
separates prose words, sentence punctuation, decimal literals and opaque
objects. Decimal identities must match in source/before/proposed/actual text.
Unicode nondecimal numerals use numeric categories, not enumerated fractions;
balanced function/subscript syntax uses the entire identifier and arguments,
not a list of function names. Mixed/unknown glyphs, fonts, drawings, images and
unproven expressions require engine/manual work. No source-restoration fallback
is used to bypass the terminal contract. Actual accepted IDs/boxes, protected
token glyph evidence, text changes and source/before/after PDF bindings reach
independent revalidation and are freshly recomputed there.

`expression_syntax.py` groups continuous arithmetic with a bounded Pratt
parser before the protected-token contract is built. It records operands,
units, unary/binary roles, precedence and parentheses as one expression tree.
A sign is not unconditionally part of the next number: `5+6` is an indivisible
binary expression, whereas a prose quantity `at +5 volts` is a signed literal.
Numerical operands connected by punctuation or implicit adjacency are also
grouped conservatively; a ratio/range or `5(6)` cannot become unrelated values.
Scientific exponent signs stay inside the number. Nested signs cannot become
safe literals merely by hiding a sign inside parentheses. Binary/ambiguous
expressions remain engine/manual work; isolated signed/grouped quantities
retain their numeric identity through repair. No document expressions are
evaluated. This supported syntax is not a universal mathematical or code parser.

An English word next to an operator or group has an unresolved semantic role,
regardless of case, whitespace, sentence shape or a following unit. `The bound
is To +23 volts` cannot be distinguished safely from an ordinary quantity by
grammar heuristics. The local edit is rejected with
`OPERATOR_ROLE_UNPROVEN_RETRANSLATE_OR_MANUAL`; the source object is retained.
Other eligible regions on the same page can still be repaired. Ordinary prose
and unsigned/scientific quantities remain eligible without role exceptions.
Font, glyph, drawing, image and compound-expression protections remain active.

Signed/grouped English quantities can be edited only after independent source
role confirmation. The development Python API `quantity_roles.confirm_from_operator`
records an explicit caller assertion bound to source SHA256, physical page,
program region, text range and glyphs. It does not infer or authenticate the
assertion. Positive tests declare their intended semantics as an external oracle;
those tests are not evidence of automatic semantic disambiguation. No model,
configuration, CLI or production path creates these records. There is no
automatic role-confirmation fallback and no approval inferred from elapsed time.

Explicit API callers must pass the same independently confirmed records as
`source_quantity_roles` to both `visual_repairer` and `program_revalidate`.
Saved repair evidence alone cannot authorize a role: independent revalidation
recomputes the proof from its explicitly supplied trusted records and the actual
source. Stale, mismatched, model-claimed or compound-expression confirmations
fail. A quantity confirmation never authorizes another mathematical object or
unknown font in the edited island. The normal production path supplies no
confirmations, so ambiguous quantities require retranslation or human work.
Numerical identity and signs use the single source edit contract; there is no
second decimal-only regex to disagree with it.

Same-region model findings and program omission warnings may share exactly one
eligible candidate. Every original finding keeps its hash, candidate binding
and pending/verified/manual disposition; empty warning replacements are never
treated as proposed translations. Conflicting candidates remain manual. A
focused image recheck, actual edited-region contract, actual omission recheck
and outside pixels must all pass before any shared finding is marked addressed.
Model clear alone cannot erase a program warning.
The limited named-operator screen is recorded separately; it cannot certify
`math_objects_passed`. That field covers eligible edited islands and unchanged
outside pixels, not universal full-paper mathematical equivalence. This
conservative restriction may reject legitimate automatic repairs, including
ambiguous parenthetical or code-like prose. Format-level contracts do not
identify arbitrary semantic mathematics written as ordinary words; independent
semantic/visual capability remains unvalidated and D02 still vetoes delivery.

Uncertainty, exhausted rounds/budget, execution errors, known regressions,
upstream failure and unvalidated audit capability all block delivery. A clear
reply cannot overwrite earlier quality failures. `execution_status`,
`audit_model_verdict`, `quality_passed` and `delivery_allowed` are distinct.

## Hash binding, interruption and delivery

The receipt binds source plus both final-PDF SHA256 values, all audited pages,
translation scope, context ID and the original candidate binding. Verify it
along with the original user translation-contract hash
immediately before delivery with `verify_before_delivery`. Changing either
final PDF or source, even only metadata bytes, invalidates the audit. A receipt
for another candidate cannot be reused.

Use `delivery_artifacts` only when `delivery_allowed=true`; retained `best.*`
and `review_artifacts` are review candidates, not automatic delivery approval.
Both CLIs refuse successful delivery exit status without the final gate.
Without `--final-audit-config`, normal processing can retain diagnostic files
but cannot produce an approved delivery.

The output directory is exclusive. It contains an execution marker, atomically
written call ledger and audit reports. `KeyboardInterrupt`/`SystemExit` leave
explicit interrupted/manual state. A process killed too early may leave a
started/unknown call; the same output directory is never automatically resumed
or overwritten. Inspect that state and reconcile usage before a separately
authorized new run. A new directory is not an implicit retry budget.

## Current limits and next evidence

Offline tests use temporary synthetic PDFs and fake clients. They validate the
orchestration, actual rendering, hash invalidation, scope, budget, interruption
and regression gates, not Luna's detection ability. Program operator and prose
screens are narrow, not semantic proofs. Existing D02 misses, D01 false positive
and three literal-valid semantic counterexamples remain unresolved evidence.

A minimal next detection falsification would use a one-page QA copy of the
existing known-bad final page plus original/dual, with no defect hints: one
vision probe and one final-page audit, at most2 native calls. Stop on a miss,
uncertainty or incomplete execution evidence. Even detection would establish
only that page result; a verified clean control and held-out relationship
contrasts are still needed to measure false positives/generalization. This is
only a proposal and has not run. The separate3-condition semantic triage draft
still tests single versus two-item context and is also unexecuted.


## rc.15 native coverage boundaries (offline WIP)

The current mapper routes actual native PDF text through `pdf_objects.py`,
`engine_source_map.py` and `semantic_objects.py`. `native_accounting_complete`
means every native text paint has a disposition, including clipped and hidden
paints. It is not a complete PDF graphics interpreter or semantic certificate.
`text_mapping_complete` additionally requires complete candidate text pairs and
all text protections. `coverage_complete` also requires no unresolved image or
vector content. Every discovered fill/stroke vector path has a geometry digest
and unresolved role; any such path blocks full coverage. Identical geometry is
not a role proof. Visible text converted to outlines therefore cannot silently
become an empty page. A genuinely blank page can have zero units; a nonempty
page requires semantic units or an explicitly verified retained-role disposition.

Canonical native glyph masks must exist for active non-whitespace primary
glyphs. Shared `[unknown]` placeholders never establish identity. Font aliases
can be bound through the actual same-source embedded program and exact Unicode
glyph masks plus the existing source geometry guard; suffix guesses are not
used. Finite clip masks are placed at the actual page origin with a one-pixel
uncertainty envelope. Uncertain clipping remains blocked. These samples do not
prove vector or mathematical equivalence.

The optional `semantic.mapping_file` binds source/target SHA256 and optional
source IR SHA256/page plus controller-selected source glyph IDs. Original-English
roles require an exact standalone sentence from the original prompt using a
closed affirmative `Preserve/Keep/Retain ... in [their] [original] English` grant.
Supported role phrases are author names/authors/their names, affiliations,
references/reference entries, source URLs/URLs, DOI, copyright statements,
license statements and publisher statements. Unsupported wording fails closed.
A translation command, a role not granted by that sentence or a grant embedded
in a negated sentence cannot authorize retaining body English.

The controller still supplies trusted role classifications and source IDs; this
syntax guard cannot prove that selected IDs really denote authors, references
or affiliations. The aggregate `original_english_scope` can represent several
roles under a recognized grant. It is not an authorization boundary against an
untrusted mapping-file author. Actual retained content must independently match
complete ordered native groups or identical native paints.

Small diagnostic subsets keep the original full translation contract. Selecting
units from physical pages 4/5 does not change the original 11-page scope, waive
other pages or create an accepted two-page final audit. Derived page copies are
viewing evidence only. None of these offline checks clears
`PROTOCOL_VALIDATED=False`, the D02 veto, historical failed controls, missing
independent factual signatures or unknown model cost.


## rc.16 final paints and release assessment

An optional `engine_target` mapping entry uses the same `path`, `sha256` and
`engine_page` binding as source IR. Optional `font_assets` maps exact final
font-resource identifiers to `{path, sha256}`. The final binder checks actual
PDF resource/program identity, Unicode, six-decimal writer baselines, size
and text direction. A discarded subset cmap alias additionally requires
single-character ActualText and matching canonical masks from both the actual
paint and the registered full font. A family name or label alone cannot bind
it. Raw native Unicode remains in the evidence. Duplicate paragraph IDs and
repeated ownership of one physical glyph fail. Matched complete paragraph IDs
from both actual views propose correspondence; they do not prove meaning,
formula roles or cross-language equivalence. Unowned groups remain explicit.

Source-prose repairs now check actual fallback-font ink after layout and actual
paint after insertion. Increased leading fixes the reproducible line-height1
CJK clipping; allowed islands, minimum font size and scale limits stay bounded.
The copier observes the native outer clip and binds retained glyph paints to
unique original native glyphs. A failed actual commit discards the candidate.
Saved source-copy records bind source/target PDF hashes, native masks, clip
bounds, renderer-owned cover geometry and the local producer. The exact
pending-file/hard-link layout is exercised before a repair-role request. Saved
records are re-read and rechecked. They are trusted local evidence, not signed
attestations; vector/raster roles and formula structure remain unresolved.

`coverage_complete=False` is a diagnostic result, not a claim that every
affected page is damaged. In particular, unclassified vector paths, missing
raster transcripts, long-unit limits and absent provenance can cause a
conservative stop without a demonstrated content defect. The strict optional
automated gate still fails closed. Under the user's release policy, a separate
documented human assessment can classify a known small visual defect, inherited
source clipping or confirmed conservative false positive as a disclosed limit.
It must not relabel unknown substantive risks as minor or mark automated
coverage as passed. Changed formula/numeric content, missing content/pages,
confirmed semantic failures and material unresolved risks require correction or
further review. Such release assessment does not validate the terminal model
protocol or erase D02, cold/cache/full-paper and independent visual test gaps.
