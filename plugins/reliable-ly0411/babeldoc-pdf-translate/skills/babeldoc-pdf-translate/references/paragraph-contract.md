# Optional native paragraph contract

For English-to-Chinese scientific prose, `provider.output_contract: paragraphs`
lets Chinese words move around complete inline math objects within one source
paragraph. The default remains `text_slots`; existing jobs keep their contract.
This option is for the native Codex/DSH bridge, not the direct HTTP translator.
Actual model validation in this candidate used Luna through Codex; DSH is covered
by deterministic protocol tests, not a new live-model acceptance.

```json
{
  "type": "codex",
  "model": "gpt-6-luna",
  "output_contract": "paragraphs",
  "retries": 1,
  "max_model_calls": 48,
  "protected_identifiers": ["L1Quad", "PID", "DOB"],
  "cache_dir": "private-cache",
  "diagnostics_dir": "private-diagnostics"
}
```

Every original paragraph has a program-owned named `row_N` string. Missing,
empty, extra or merged rows fail. Each connected formula run, its internal
brackets/operators and internal styles become one opaque token. Prose can
reorder complete groups inside the same external style segment; internal group
spelling and external style boundaries remain exact. Short headers and table
labels keep all token order. Per-row required-token manifests and correction
feedback identify missing, repeated or borrowed tokens. The correction is still
bounded by `retries` and the overall native-call cap. Numeric values/counts,
units and explicitly protected names remain checked after program restoration.
If translated prose moves away from between two complete objects, their target
run must partition exactly into the original objects in the same style segment.
This permits adjacency without treating it as a newly generated formula. No
internal character, operator, bracket or object can be changed, added or lost.
Semantic relationships and actual glyph placement still need rendered review.

The rc.3 name-accounting revision recognizes a narrow wrapped spelling such as
configured `Lipschitz` rendered by extraction as `Lip- schitz`, or an explicit
soft hyphen. It counts only configured, unhyphenated ASCII capitalized words,
with at least two letters on each side of a lowercase/lowercase split. An ASCII
hyphen requires following ASCII break whitespace. Real/nonbreaking/minus
hyphens, compound IDs, math/style splits, assignments, backtick code and URLs
are not joined. A configured literal hyphenated alternative vetoes the alias.
This temporary view is used only for name counts, never to rewrite source,
model input, code, math or PDF glyphs. Omitted/duplicated names and math still
fail. Only affected requests receive a wrapped-name cache revision; unaffected
cache identities remain unchanged. Source-prose repair uses the same accounting.

The rc.2 paragraph schema revision is `named-paragraphs-schema-5`. Configured
whole names use `pdftranslate_name` tokens and may follow Chinese word order
relative to math inside the same actual style/code segment. Assignments and
split-name fragments remain `pdftranslate_code` objects. Name counts, relative
name/style/code order and short-header token order stay exact. `barrier_tokens`
in each row explicitly lists the fixed external boundaries; names are not code
barriers. A rejected token/barrier check reports the affected row and guard.
The contract also checks
braces, square delimiters, operators and unmatched parentheses in generated prose;
balanced parentheses for bilingual terms remain allowed. A closing function
delimiter wrongly classified as ordinary text must be repaired in the engine,
not silently dropped by the translator or ignored by the guard. A v3/v4 cache entry
is reused only after its request/content checksums and **current** guards pass.
A semantically rejected legacy entry stays untouched and allows the normal bounded
fresh request; corrupt entries fail closed. Legacy hits/refusals are separate metrics.

A source `{v3}Quad` is not a source literal `L1Quad`. The `Quad` fragment stays
attached to its formula; the model cannot add another complete `L1Quad` or
decode the hidden prefix. An explicitly configured single-letter math prefix
such as styled `L` adjacent to `{vN}` belongs to that same opaque object. Explicit
uppercase names followed by a lowercase prose suffix, such as `DOBmethods`, are
counted as `DOB` plus prose. This exception does not turn unknown capitals into
protected names or match `MMLU` inside `MMLU-Pro`.

Paragraph and text-slot caches are separate. A validated paragraph response
remains reusable after extra corrective diagnostics; it must pass the same
current fidelity guards on every cache read. The name-fragment, glued-acronym
and styled-prefix revisions invalidate only requests affected by those cases.
Cold tests require a genuinely new cache directory. A recovery using earlier
successful requests is a resumed run, even if its output directory is new.

Native CLI invocation counts are not a count of backend HTTP attempts: the CLI
may reconnect internally within its timeout. A known recoverable stream/server
error before a final `turn.completed` can proceed to strict JSON, tool-use and
fidelity checks. Unknown/fatal errors or errors after completion still fail.
Only error classes, event types and hashes are recorded; raw native stderr is
not persisted. Missing usage is unknown, never zero. Private opt-in diagnostics
capture failed requests even when no response was produced.
Opt-in diagnostics also write a metadata-only attempt journal **before** each
client invocation and atomically update it on return. A process interrupted after
the start record has uncertain usage, never zero usage. Journals do not contain
prompts, document text, native stderr or credentials.

This protocol cannot prove semantic completeness or readable typesetting.
Run the [visual workflow](visual-review.md), then independent source-to-output
acceptance. The L1Quad corpus currently remains an incomplete acceptance case;
see its [results](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10).
