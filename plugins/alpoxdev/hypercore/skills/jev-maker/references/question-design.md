# Question Design Reference

A Jev request is a `state` plus a map of typed questions, and the questions decide whether the
answers are usable. Each question should ask for one narrow judgment, carry its whole meaning in
`instructions`, and draw a clear line between neighbouring options. This file covers those habits,
the extraction pattern that keeps code in control, what to do with Korean input, the known
limitations of the current model version with a workaround for each, and a checklist a person can
run by hand when the offline checker is not available.

Prices, limits, and model ids are in the platform snapshot linked at the end, not here.

## Contents

- The question id never reaches the model
- One judgment per question
- Structured instructions
- Choice criteria: what, not_for, examples
- Score levels as situations
- Noul true and false descriptions
- Candidate extraction
- Korean input
- jev-1.13 limitations and workarounds
- Request validity checklist
- Sources

## The question id never reaches the model

The vendor states that a question id "is not sent to the underlying model and is not used in
inference" (api, 2026-10-01). An id such as `refund_requested` is a label for your code and
nothing more. The model reads `instructions`, so the whole question has to live there. When an id
looks self-explanatory, that is exactly when a thin instruction slips through and the model
answers a question nobody wrote.

## One judgment per question

Ask for something a knowledgeable person settles in a second once the context is in front of
them. "Does this message convey urgency?" is that kind of question. "Analyze this message and pick
the best course of action" is not; it needs slow reasoning and belongs in code.

When a judgment depends on several independent factors, ask about each factor separately and
combine the answers in your own logic. One question per factor keeps a wrong answer traceable to
the factor that produced it. A blended question hides which part failed.

Send the questions together in one request. Every question sees the same state and answers
independently, so adding questions barely changes the response time, and a question you might not
need costs almost nothing.

## Structured instructions

`instructions` accepts a string, an object, or an array. Keep a short, unambiguous question as a
string. Reach for structure in three cases: the question needs background or examples, part of the
question comes from your code, or several questions share similar wording and need separating.

Put the question in one field and the data it refers to in the others. The JSON blocks in this section
and in the Choice criteria section are question fragments, not whole requests, so each one goes under
`questions` in a request:

```json
"same_as_record": {
  "type": "noul",
  "instructions": {
    "potential_duplicate": { "name": "John Smith", "location": "Oakland, California" },
    "question": "Is the resume for the same person as `potential_duplicate`?"
  }
}
```

A complete minimal request holds `state`, `model`, and `questions`, and it passes the checker on both
direct routes:

```json
{
  "state": "Payouts have been failing since Monday.",
  "model": "jev-latest",
  "questions": {
    "needs_human": {
      "type": "noul",
      "instructions": "Does this ticket need a human agent, rather than an automated reply?"
    }
  }
}
```

When a question is about one part of a structured state, name that part by path inside backticks,
as in "Does `ticket.messages[0].text` request a refund?". The path tells the model which slice of
the state to judge and keeps the rest of the state out of the decision. A value that comes from a
database goes into its own named field rather than into a string template, so the code can swap
the value without rewriting the question.

## Choice criteria: what, not_for, examples

A Choice question returns the option with the highest probability, so the options have to be
separable. Each option's description can be an object that says what the option covers, what
belongs to a different option, and a few examples. This block is the `criteria` fragment of one
question, not a whole request:

```json
"criteria": {
  "card_setup": {
    "what": "Purpose, eligibility, or setup",
    "not_for": "Quantity, transaction, or merchant restrictions",
    "examples": ["How can I get a disposable virtual card?"]
  },
  "card_limits": {
    "what": "Quantity, transaction, or merchant restrictions",
    "not_for": "Purpose, eligibility, or setup",
    "examples": ["How many can I make per day?"]
  }
}
```

Use the same field names across every option so the model can compare them directly (`not_for` is
the field name this package uses; the vendor pattern is the three-part description). The contrast
matters most for options that are easy to confuse.

Add a fallback option such as `other` or `none of the above` whenever the list might not cover
every input, so a request that fits nothing is reported rather than forced into the nearest listed
option. The offline checker warns with `NO_FALLBACK_OPTION` when a Choice has no `none`, `other`,
or `unknown` key; that check is a heuristic, not a vendor rule.

## Score levels as situations

A Score returns a probability-weighted position along ordered levels, and the position can land
between two levels. Write each level as a situation a person could point at, not as an intensity
word. "Very angry" means something different to every reader; "uses strong language and repeats
the complaint" does not. Give each level a description and, where it helps, example situations, and
always define the low end so the middle of the scale has somewhere to sit.

Levels are weak for recovering an exact number: an in-between score is possible, but the number is
not a precise measurement of the underlying value. Use a Score to clear a threshold or to sort, never
to reconstruct a quantity.

## Noul true and false descriptions

`criteria` is optional for a Noul. When you write it, the only allowed keys are `true` and `false`,
and each holds a string, an object, or an array describing what that side means in your domain.
Treat the criteria as an extension of the instruction and align the wording of the two; a Noul
whose `true` side reads like a no is a known failure mode.

A Noul returns the probability that the answer is yes, and nothing else. A value near 0.5 means
the model gives yes and no equal weight, which is uncertainty rather than a medium-strength answer.
When you need a degree instead of a yes/no, use a Score with defined levels.

## Candidate extraction

The model does not generate text well and does not count reliably. Both jobs go to code. The
extraction pattern keeps the model on the part it does well:

1. Code enumerates candidates for the value you want, with a regular expression, a parser, or a
   generative model that proposes options.
2. Jev picks among the candidates with a Choice question whose options are the candidates.
3. Code copies the chosen value verbatim from the candidate list and normalizes it.

The vendor recommends exactly this split: "extract possible options using regex or a generative
model and let jev-1.13 pick the correct extraction" (jaggedness, 2026-10-01).

Measure the two halves apart, because they fail for different reasons:

- **Candidate coverage**: does the true value appear among the candidates at all? A low number
  here is a code problem in the enumerator, and no question wording will fix it.
- **Selection accuracy**: given the true value was among the candidates, did the model pick it?
  A low number here is a question problem, usually options that are hard to tell apart.

A single end-to-end accuracy number hides which half is broken. Report both, and fix the failing
half.

## Korean input

Write instructions in English by default. English is the vendor's primary training language and
where accuracy is best; other languages, including CJK scripts, are handled but not equally well
(models, 2026-10-01).

Keep the state in the language it arrived in. Translating the content under judgment changes the
evidence being judged, and the model reads the state as it is given.

Because the language is outside the vendor's best-supported range, treat Korean input as unproven
until you have tested it:

1. Run a pilot over your own Korean content, with labels you trust.
2. Compare the answers against those labels and record where they disagree.
3. Keep a confidence gate that sends low-confidence answers to a person, and widen the review band
   while the evidence is thin.
4. Pin a versioned model id once thresholds are tuned, so a silent alias move cannot change them.

## jev-1.13 limitations and workarounds

The vendor lists nine known failure modes for this version and a workaround for each (jaggedness,
2026-10-01). The design consequence is the same throughout: give the model the judgment, keep the
computation in code.

| Failure mode | Workaround in the question design |
| --- | --- |
| Literal reading: the answer follows the words, not the intent | Write the exact condition in `instructions` and put boundary cases in the criteria |
| Math and numbers: counting and numeric representations are unreliable | Count and compute in code; send names or buckets instead of hex or binary values |
| Date and time comparison: dates are read as text, not as ordered quantities | Extract each date part with a Choice over a closed set, then compare in code |
| Indirection: double negatives and multi-hop questions lose accuracy | Cut the hops and name the relevant state paths directly |
| Large state full of irrelevant detail: unrelated content distracts | Filter in code and send only the fields the question needs |
| Adversarial content: state is data and is not treated as hostile | Write precise criteria and test the edge cases before shipping wide |
| Contradictory instructions and criteria: the two can fight | Align the criteria with the instruction and read both aloud |
| Common-sense structural invariants: a question and its negation need not sum to one | Do not move a threshold from one question or type to another |
| Generation: the model is not trained to produce text | Use the extraction pattern above, with code owning the text |

One more, from the same page: a Score output is weak for recovering an exact number between two
levels. It can decide whether a value clears a threshold, but not rebuild the value.

## Request validity checklist

Run this list by hand when the offline checker cannot run, for example where bash or jq is not
installed or the checker has been removed. It mirrors the checks in `../scripts/check-jev-request.sh`
one for one, including the error codes that script prints.

**The document**

1. The file is valid JSON. Otherwise `INVALID_JSON`, or `INPUT_TOO_DEEP` when the document nests
deeper than the checker's parser can read.
2. The root is a JSON object, not an array or a scalar. Otherwise `ROOT_NOT_OBJECT`.
3. `state` is present and is a string, an object, or an array. `null`, numbers, and booleans are
   rejected. Otherwise `STATE_MISSING` or `STATE_TYPE`.
4. `model` is a non-empty string. Otherwise `MODEL_MISSING`.
5. The model id fits the route. Direct: the id starts with `jev-` (an unverified alias warns with
   `MODEL_UNVERIFIED`). b.ai: exactly `jev-1.13.0` or `jev-latest`. AI SDK: any non-empty string.
   Otherwise `MODEL_UNSUPPORTED`.

**The questions map**

6. `questions` is a non-empty object. Otherwise `QUESTIONS_MISSING` or `QUESTIONS_EMPTY`.
7. Every id holds non-whitespace text. Otherwise `QUESTION_ID_BLANK`.
8. Every entry is a JSON object. Otherwise `QUESTION_NOT_OBJECT`. A missing `type` or `instructions`
   field is caught by items 9 and 10 below, not by this code.
9. `type` is one of the route's names. Direct and b.ai: `noul`, `choice`, `score`. AI SDK:
   `boolean`, `choice`, `score`. Otherwise `QUESTION_TYPE`.
10. `instructions` is present and is a string, an object, or an array. Otherwise
    `INSTRUCTIONS_MISSING` or `INSTRUCTIONS_TYPE`.

**Criteria, by question type**

11. Yes/no (`noul`, or `boolean` on the AI SDK route): criteria is optional; when present each key is
    `true` or `false` and either key may be omitted, so an empty object and a one-key object both pass.
    Each present value is a string, an object, or an array. Otherwise `NOUL_CRITERIA_TYPE`,
    `NOUL_CRITERIA_KEY`, or `NOUL_CRITERIA_VALUE`.
12. `choice`: criteria is a required object with 1 to 255 options; each option description is
    `null`, a string, an object, or an array. Otherwise `CHOICE_CRITERIA_MISSING`,
    `CHOICE_CRITERIA_COUNT`, or `CHOICE_CRITERIA_VALUE`.
13. `score`: criteria is a required array of 2 to 10 items, each a string, an object, or an array
    and never `null`. Otherwise `SCORE_CRITERIA_MISSING`, `SCORE_CRITERIA_COUNT`, or
    `SCORE_LEVEL_TYPE`. On the AI SDK route a count above 10 is a warning, because that route
    documents no upper bound but the request stops being portable.

The 255-option and 2-to-10 bounds in items 12 and 13 are what the offline checker enforces. For
the vendor statement behind them, read
[the platform snapshot](../references/official/jev-platform.md). The ban on a `null` description for
a yes/no criteria value and for a score level is the checker's own constraint, matching the direct
route's pages; the AI SDK route allows `null` descriptions, so it is not an AI SDK rule.

**Route-specific and cross-cutting**

14. On b.ai, `stream` is absent or `false`. Otherwise `STREAM_NOT_SUPPORTED`.
15. No string value in the document looks like a credential; object keys are not scanned, and the
    value itself is never echoed. Otherwise `SECRET_IN_REQUEST`. The checker matches a `sk-` prefix
    followed by 16 or more alphanumerics, and the case-sensitive pattern `Bearer ` followed by 16 or
    more characters from `[A-Za-z0-9._-]`.

**Warnings the checker raises without failing the request:** `UNKNOWN_TOP_LEVEL_FIELD` for a
top-level key outside `state`, `model`, `questions`, and `stream`; `NO_FALLBACK_OPTION` for a
Choice that has 1 to 255 options and none of `none`, `other`, or `unknown`; `STATE_LARGE` when a
length-divided-by-four estimate puts the state plus the longest question over the API budget; and
`MODEL_UNVERIFIED` for a direct-route alias outside the known list.

**Exit codes.** 0 when there are no errors, 1 when there is at least one error including an
unparsable file or a document nested past the checker's parser depth limit, and 2 for a usage problem (no file
argument, an unreadable file, or an unknown route). Run it from the skill folder as:

```bash
bash scripts/check-jev-request.sh --route direct path/to/request.json
```

Treat a green run as a check on shape only. A well-formed request can still be a bad question, and
which of those two you have shows up only against labeled data.

## Sources

> Links checked 2026-10-01

| Claim | Source |
| --- | --- |
| A question id is not sent to the model and is not used in inference | <https://docs.typesafe.ai/api> |
| `instructions` accepts a string, an object, or an array, and can be split into a question field and data fields | <https://docs.typesafe.ai/api> |
| Structured instructions, contrastive Choice criteria with what, not_for, and examples, and state paths in backticks | <https://docs.typesafe.ai/concepts/how-to-build-with-system-one> |
| Choice, Score, and Noul guidance, the `other` or `none of the above` option, and the meaning of 0.5 on a Noul | <https://docs.typesafe.ai/primitives> |
| Confidence belongs to Choice and Score answers only | <https://docs.typesafe.ai/confidence> |
| The nine failure modes, their workarounds, the extraction split with code, and the weak Score interpolation | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| English as the primary training language and the caution on other languages, including CJK | <https://docs.typesafe.ai/models> |
| The cookbook inventory used to name the recipes in the sibling patterns file | <https://docs.typesafe.ai/llms.txt> |

The checklist mirrors the local checker at `../scripts/check-jev-request.sh` in this package, read
on 2026-10-01.

### Evidence grade

`PRIMARY` for the design rules above: each traces to a vendor page captured on 2026-10-01 and
listed in the table. `LOCAL` for the request validity checklist, which is a restatement of the
repository checker's own rules and error codes rather than a vendor claim; the checker itself cites
the same vendor pages for the request shape it enforces.

Not covered here and deliberately left to the snapshot: prices, rate limits, model ids, endpoints,
and the per-route contract differences.
