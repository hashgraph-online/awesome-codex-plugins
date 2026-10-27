# Explicit identifier fidelity and spending bounds

The native bridge can preserve a caller-selected list of ASCII names as literal
program-owned text. This is useful when a benchmark/model name must survive
translation even if the prose around it changes. It is separate from a glossary,
whose instructions a model can still omit. Names remain in their source form.

```json
{
  "type": "codex",
  "model": "gpt-6-luna",
  "max_model_calls": 80,
  "protected_identifiers": ["MMLU", "MMLU-Redux", "MMLU-Pro"]
}
```

Add these fields to the job's existing `provider` object. The three names above
are the actual R1 regression case, not defaults for every PDF. Do not use broad
all-capital-word heuristics: headings and ordinary prose must remain translatable.
Names are explicit, unique strings (up to 128, each at most 100 ASCII characters).
Longest literal matches win; MMLU is not treated as the prefix of MMLU-Redux.
The bridge masks selected names, owns their restoration, and checks exact
occurrence counts for both batch and recognized single-paragraph requests.
This does not protect arbitrary unlisted facts or guarantee faithful semantics.

An actual R1 paragraph retained `MMLU-Redux` and `MMLU-Pro` but omitted the base
`MMLU`, while all style/formula markers remained valid. Original-text reflow
retained all three. The explicit-name regression rejects that formerly accepted
reply. Cache identity gains the matched names and protection revision only when
the request contains a selected identifier; unrelated checkpoints keep their
identity. Invalid cache integrity still fails closed.

A configured name may be split by a formula marker: the real L1Quad failure
contained `{v3}Quad`, while the model added a literal `L1Quad` and lost `Quad`.
Do not remove the name-count guard to accept that reply. The bridge now owns a
literal prefix/suffix of an explicit configured name immediately beside `{vN}`,
restores it beside the same marker, and rejects additions, loss or movement.
It never guesses the formula's hidden text. Affected requests gain a fragment
revision in their cache identity; unrelated valid checkpoints are retained.
The existing bounded retry also explains the split-name constraint explicitly.

`max_model_calls` bounds native **attempts**, including unsuccessful/retried
attempts, for one bridge/job. Cache hits do not spend a call. The default cap is
512; set a smaller task-specific cap. The total job timeout and each native
timeout remain independent bounds. Restarting a job creates a new per-run budget;
retain checkpoints and review cumulative usage before enlarging a run.

Token counters remain native counters; cached input is a subset, not a new total
to add to input. Missing counters or an unknown subscription dollar price stay
unknown. The bridge cannot guarantee a hard monetary cap without a priced route.
# Closed calendar literals

Named Gregorian dates are compared as typed dates at the same precision.
For example, `September 2025` and `2025年9月` represent the same month;
`18 September 2025` and `2025年9月18日` represent the same day. Standard named
month abbreviations and Chinese month/day numerals are supported. Changed
months/years, added days, impossible dates and extra numeric values are rejected.

The bridge and source-prose checks share the audit's pure date parser. Translation
guards leave unlabelled numeric ISO strings numeric, so a subtraction or model
identifier cannot gain a date exemption. Opaque math fragments are never decoded
to infer a missing year. Scalar values, signs, units, marker identity and source-gap
numeric order retain their checks. All on-disk cache content is revalidated under
the current contract; existing valid checkpoints need no global invalidation.

This fixes the real cold-run refusal of the legitimate header translation
`September 2025` → `2025年9月`. It does not waive an arbitrary extra numeral
or establish the semantic relationships surrounding a date.
# Bounded source-owned style restoration

Paragraph replies can omit the first opening style tag. The decoder restores
that single source token only when the source begins with one simple prose span,
the target has nonempty prose before the matching close, and its entire remaining
marker sequence exactly equals the source sequence after that opener. It never
adds words, closing tags, inner tags, numbers or math. Source before/after hashes
and subsequent guard outcome are recorded. Every original guard still applies.

For a format/fidelity error, the existing one bounded correction may request
named text slots from the same native model. The program restores source tags
and objects, then validates the usual external paragraph contract. The attempt
journal records the actual schema. A transport retry retains its original schema.
There is no extra retry, different model, numeric waiver or global cache reset.

Old failed runs remain failed. Reusing a previously returned raw reply after
this deterministic restoration is explicitly checkpoint recovery, with original
reply/request/journal hashes and zero new inference; it is not a fresh cold run
or rendered/semantic acceptance.
# rc22: calendar fields that remain native PDF objects

Date checking runs before formula placeholders are removed. A hidden day/year
is represented by its exact original `{vN}` identity and calendar role, never by
a guessed numeric value. Closed English named-month and Chinese 年/月/日 forms
support literal or opaque days/years and Arabic/Chinese month spellings. Month,
known day/year, precision, field identity and multiplicity must agree. An
impossible date cannot fall back to a shorter month match. Bare numeric ISO
expressions remain numeric in translation guards, and signed components do not
gain a date exemption. Context such as `May {v1} be independent?` stays prose.

Only two fields inside the same recognized date may be separated by calendar
punctuation without being fused into a mathematical run. Adjacent operators,
tuples, unrelated objects, style boundaries and native marker order retain
their existing protection. Native date field reordering remains conservative;
the supported Chinese month/day/year spelling can retain source marker order.
Unanchored month-only fragments and ambiguous names are not inferred as dates.

New explicit ellipsis omission signals are rejected; existing ellipses may
change typographic spelling. Source-gap scalar checking retains signs and
exponents. These checks detect structural/content symptoms; they do not prove
all prose was translated or that semantic relationships are correct. Actual
rendered review and the bounded semantic repair loop remain necessary.

Alphanumeric reference counts are program-computed prompt and error metadata.
They identify a repeated model/version name separately from a changed scalar;
they grant no exception to either protection. Chinese may express an implied
subject using a pronoun. Expanding that subject into another `Dev1` occurrence
remains conservatively rejected, even when the prose could be semantically
equivalent; the bounded correction now receives that specific cause. Failed
native replies with a corrected calendar row and a still-rejected body row
must not be reused as successful cache entries.

The scalar lexer is shared by the bridge and source repair. Unicode mathematical
minus and ASCII minus denote the same sign; deleting either sign or changing an
exponent is rejected. No numeric rounding, value substitution, global name
exemption or broad date allowance is introduced.

rc.23 keeps content corrections in the paragraph schema. Only an explicit JSON,
row/slot, or marker-boundary defect selects the one bounded fixed-slot recovery.
Typed source-calendar hints expose visible month values and precision, never
decode an opaque PDF year/day. Hints do not authorize a changed value: the same
original-source guards run after both attempts. Cache entries remain subject to
those guards. No failed reply is promoted into a successful cache entry.
