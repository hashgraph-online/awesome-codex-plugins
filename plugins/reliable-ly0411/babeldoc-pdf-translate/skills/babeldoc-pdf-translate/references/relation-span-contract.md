# Offline literal-span contract

`relations-spans-v3`, contract SemVer `3.0.0-draft.1`, is an offline proposal in
`scripts/semantic_relation_spans.py`. The plugin stays at `1.5.0-rc.5`; this is
not a frozen or published candidate. Production configuration still accepts
only its existing protocols. There is no model, transport, PDF, cache or repair
entry point in the new module.

The failed `relations-v2` experiment, its code, frozen packets and 10/12 evidence
result remain unchanged. New format examples are authored offline; they are
never described as repaired model replies or a passing rerun.

## Representation and checks

Each context, role fragment and attachment has `start`, `end`, and `text`.
Offsets count Unicode code points in the original complete paragraph, including
spaces and protected-token characters. Start is inclusive and end exclusive.
Boolean/floating offsets, normalization, invented text and partial opaque tokens
fail. Explicit offsets can distinguish repeated identical words.

Each subject/predicate/object contains at most six exact fragments in original
order. Fragments cannot overlap or be reused in another role in the same
evidence record. An attachment has a kind, a named head and one literal span;
attachments must also be ordered and disjoint. Every lexical character and
opaque token between fragments of one role needs an explicit attachment to
that role. A generated explanation does not bind or cover a gap.

For the miniature paragraph `可以在{v3}中使用`, a predicate can be represented as:

```json
{
  "context": {"start": 0, "end": 10, "text": "可以在{v3}中使用"},
  "roles": {
    "subject": [],
    "predicate": [
      {"start": 0, "end": 2, "text": "可以"},
      {"start": 8, "end": 10, "text": "使用"}
    ],
    "object": []
  },
  "attachments": [{
    "kind": "reference_scope", "head": "predicate",
    "span": {"start": 2, "end": 8, "text": "在{v3}中"}
  }]
}
```

The concatenation `可以使用` is still not accepted as an original quotation.
Neither word order nor the intervening reference can be supplied by commentary.

Contexts across all claims must cover every lexical character and complete
opaque token in each whole paragraph. This retains the D02 coverage veto and
adds explicit opaque-token coverage. Non-metadata contexts require a predicate;
only a missing target claim permits a null target context. Changed/missing and
uncertain claims constrain the row conclusion. Summary and explanation strings
are never used as source anchors or coverage evidence.

## Replaying the failed trial

`lift_v2_exact` is a mechanical offline adapter. It lifts an old exact contiguous
role to one coordinate span only when its location is unambiguous. It never
splits, paraphrases, searches explanations or reconstructs a missing role.

The 12 observed replies retain ten literal-valid rows and the same two failures.
Raw D04 still fails the lift. A separate human-authored D04 example demonstrates
that two exact fragments plus the reference attachment can express its natural
Chinese predicate. Raw D02 remains missing actual role evidence and complete
quote coverage. Even a deliberately vacuous literal-role probe cannot overcome
its old source319/371 and target97/112 quote-coverage gaps. This probe is a test
of the veto, not a correction or a semantic witness.

## Limits and the next experiment

Literal support does not prove the declared relationship. Three new authored
counterexamples (actor swap, negation omission and reference-role swap) can have
valid literal spans and a wrong equivalent conclusion. The offline validator
cannot detect that semantic falsehood; `protocol_validated=false` and the
known-regression veto continue to block promotion. Context coverage also does
not prove that every proposition received a correct role analysis. Punctuation,
operators outside opaque tokens, formulas, images and PDF layout retain their
separate audits. Do not use single characters or attachment labels as a way to
claim semantic correctness.

Offline controls are author-aware tests, not independent blind generalization
evidence. A new input/evaluator registration proposes at most two isolated Luna
calls with six distinct sources each, twelve judgments total. No native calls
are authorized or made by this stage. Stop before the next arm on any false
positive, false negative, uncertainty, invalid/incomplete evidence, missing
usage or changed sealed artifact. No output repair, retry or post-result rule
change is allowed. Money remains unknown; any future execution needs its own
explicit budget and a sealed transport runner before its first invocation.

Reproduce the focused offline checks with:

```text
python -m unittest discover -s tests -p test_semantic_relation_spans.py -v
```

Use the configured non-Store Python/runtime for full upstream regression tests.
No model credentials, network access or PDF rendering is needed for these checks.

## Subsequent native pilot

After a separate authorization and execution seal, the six-row ArmA pilot used
one native Luna/high call and failed. Raw TP2/TN2/FP1/FN1, literal evidence1/6;
ArmB was not run and the unused call was not spent. D02 was missed and D01 was
a false positive. The one literal-valid D04 row did not use multiple fragments
and left some meaning only in broad context. It therefore does not validate
complete proposition coverage or native multi-span predicates. The contract
version/scorer remain unchanged, the trial remains failed and quality stays
blocked. See the [actual result](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/10).
