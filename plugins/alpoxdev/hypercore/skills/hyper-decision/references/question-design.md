# Question Design Reference

A decision request is one shared input plus a set of typed questions, and the questions decide
whether the answers are usable. Each question should ask for one narrow judgment, carry its whole
meaning in its own instruction text, and draw a clear line between neighbouring options. This file
covers those habits, the neutral type names and the dialect each route uses, the state that the
questions are asked about, the extraction pattern that keeps code in control, what a refusal means,
and a checklist a person can run by hand when the offline checker is not available.

Prices, limits, and model ids are in [`./providers.md`](./providers.md) and the snapshots under
[`./official/`](./official/), not here.

## Contents

- The human test for the state
- Judgments in the model, decisions in code
- Neutral types and the dialect they travel in
- The question id is a label
- One judgment per question
- Structured instructions
- Choice criteria
- Fallback options: a companion boolean first
- Score levels as situations
- Boolean true and false descriptions
- Box questions
- Option order is a measurable bias
- Refusals are not low probabilities
- Encoding the state
- Candidate extraction
- Korean input
- Documented weak spots
- Request validity checklist
- Sources

## The human test for the state

The state is the part of the request that most often decides quality, and the test for it is simple:
could a capable person, shown only this state and this question, answer it quickly and by intuition?
When a question fails that test, the fix is usually in the state rather than in the wording.

- Give what a person would look at: who sent each message, the full thread rather than a truncated
  last line, names rather than raw ids or markup, and the item the question is about rather than the
  whole catalogue.
- State facts the code already knows, such as "every message in `replies` arrived after the refund
  was issued", instead of leaving the model to rediscover them.
- Supply what the model cannot know, such as what an internal product code refers to.
- Keep every field relevant. A field added for one question can sway the answer to another, and the
  vendor lists a large state full of irrelevant detail as a documented weak spot.

Source: <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) and
<https://docs.typesafe.ai/model-jaggedness.md>.

## Judgments in the model, decisions in code

Ask for the judgments the decision depends on, and keep the decision itself as a table in code. A
question that asks the model to make the decision, such as "should this ticket be escalated?", is
usually at the wrong layer: the answer is a policy that belongs in code, where it is visible and
testable, and the model should supply the inputs that policy reads.

Write the table out as you design. A combination of judgments with no defined outcome is a design
gap in the system, and it is better settled in code than papered over with a broader question.

Source: <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## Neutral types and the dialect they travel in

Four neutral types cover every verified route. The wire name and the container shape change with the
dialect, so a question set written for one route is not a question set for another.

| Neutral type | Asks for | System One dialect | OpenAI Decisions dialect | AI SDK |
| --- | --- | --- | --- | --- |
| `boolean` | one P(true) scalar | `noul` | `predicate` | `boolean` |
| `choice` | one option from a closed set, with a distribution | `choice` with `criteria` as a map of option to description | `choice` with `choices: [{ value, description }]` | `choice` |
| `score` | a position on an ordered scale, with a distribution | `score` with `criteria` as an ordered array of level descriptions | `score` with `levels: [{ label, description }]` | `score` |
| `box` | four edges around something in an image | `box`, Jev 1.14 only | not supported | `box` in the contract, TypeSafe provider only |

- The System One dialect is the one to hold in mind while designing, because its option map is the
  friendliest to write. Convert at the boundary, not in the design notes.
- On the OpenAI dialect the question container is an array rather than a map, each entry carries a
  required `name`, and there is no `criteria` field anywhere; a question that carries one is
  rejected by the checker with `CRITERIA_NOT_SUPPORTED`.
- The AI SDK passes the question through to whichever provider answers, so the question type support
  is a property of the provider, not of the SDK. The Anthropic and Google adapters return no
  distributions at all.
- `box` is a single vendor's feature on hosted routes. Treat it as an experiment with an image
  requirement, not as part of the general contract.

Source: <https://docs.typesafe.ai/primitives.md>, <https://developers.openai.com/api/reference/resources/decisions/methods/create.md>,
and <https://ai-sdk.dev/docs/ai-sdk-core/decisions>.

## The question id is a label

On the System One dialect the question container is a map of id to question, and the vendor's API
page captured on 2026-10-01 states that an id "is not sent to the underlying model and is not used in
inference". The pages this package captured on 2026-11-08 describe the map and its minimum size but
do not repeat that sentence, so treat id visibility as a vendor statement from that date rather than
a contract you can rely on.

On the OpenAI dialect each question needs a `name`, and the answer echoes it back. Whether that
`name` reaches the model is not documented in the pages captured here; the reference describes it as
the identifier of the answer.

Either way the design rule is the same: the model reads the instruction text, so the whole question
has to live there. An id such as `refund_requested` is a label for code, and an id that looks
self-explanatory is exactly when a thin instruction slips through and the model answers a question
nobody wrote.

Source: <https://docs.typesafe.ai/api/system-one.md> and
<https://developers.openai.com/api/reference/resources/decisions/methods/create.md>.

## One judgment per question

Ask for something a knowledgeable person settles in a second once the context is in front of them.
"Does this message convey urgency?" is that kind of question. "Analyze this message and pick the best
course of action" is not; it needs slow reasoning and belongs in code.

When a judgment depends on several independent factors, ask about each factor separately and combine
the answers in your own logic. One question per factor keeps a wrong answer traceable to the factor
that produced it. A blended question hides which part failed.

Send the questions together in one request. Every question sees the same state and answers
independently, so adding questions barely changes the response time, and a question you might not
need costs almost nothing.

## Structured instructions

`instructions` accepts a string, an object, or an array on every dialect that has the field. Keep a
short, unambiguous question as a string. Reach for structure in three cases: the question needs
background or examples, part of the question comes from your code, or several questions share
similar wording and need separating.

Put the question in one field and the data it refers to in the others. The JSON blocks in this
section are question fragments, not whole requests, so each one goes under the question container of
a request:

```json
"same_as_record": {
  "type": "noul",
  "instructions": {
    "potential_duplicate": { "name": "John Smith", "location": "Oakland, California" },
    "question": "Is the resume for the same person as `potential_duplicate`?"
  }
}
```

A complete minimal request in the System One dialect holds `state`, `model`, and `questions`:

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

The two model ids above are one vendor's; the ids each route accepts, and their dates, are in
[`./official/jev-platform.md`](./official/jev-platform.md) and
[`./official/openai-decisions.md`](./official/openai-decisions.md).

The same question in the OpenAI dialect moves the input to `input`, names the question, and drops the
map. The `input` value can be a string, an array of input items, or a JSON object passed as
`input_json`:

```json
{
  "input": "Payouts have been failing since Monday.",
  "model": "gpt-6-luna",
  "questions": [
    {
      "type": "predicate",
      "name": "needs_human",
      "instructions": "Does this ticket need a human agent, rather than an automated reply?"
    }
  ]
}
```

When a question is about one part of a structured state, name that part by path inside backticks, as
in "Does `ticket.messages[0].text` request a refund?". The path tells the model which slice of the
state to judge and keeps the rest of the state out of the decision. A value that comes from a
database goes into its own named field rather than into a string template, so the code can swap the
value without rewriting the question.

Source: <https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md> and
<https://docs.typesafe.ai/primitives/advanced.md>.

## Choice criteria

A Choice returns the option with the highest probability, so the options have to be separable. Each
option's description can be an object that says what the option covers, what belongs to a different
option, and a few examples. This block is the `criteria` fragment of one System One question, not a
whole request:

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

Use the same field names across every option so the model can compare them directly. `not_for` is
the field name this package uses; the vendor pattern is a three-part description. The contrast
matters most for options that are easy to confuse.

On the OpenAI dialect the same content becomes a `choices` array, and the description is a plain
string or an object:

```json
"choices": [
  { "value": "card_setup", "description": "Purpose, eligibility, or setup. Not for quantity, transaction, or merchant restrictions. Example: how can I get a disposable virtual card?" },
  { "value": "card_limits", "description": "Quantity, transaction, or merchant restrictions. Not for purpose, eligibility, or setup. Example: how many can I make per day?" }
]
```

Give the model the whole list rather than a shortlist. The vendor states that a Choice accepts up to
255 options and that adding options costs a few tokens each, so a full set of teams, categories, or
products is cheaper than a misclassification caused by a truncated list.

Source: <https://docs.typesafe.ai/primitives/choice.md>,
<https://docs.typesafe.ai/primitives.md>, and
<https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions>.

## Fallback options: a companion boolean first

A Choice always returns one of its options, even when nothing fits, and a Box always returns four
edges, even when the object is absent. Something has to carry "none of these" out of the request,
and there are two ways.

- **A companion boolean, which this package recommends as the default.** Ask a second `boolean`
  question over the same state: "does any of the listed options fit?". The vendor's own guidance is
  that an `other` option competes with the real options for probability, which is why it now favors
  the companion question, and it says this "works better" in its tests than an `other` or
  `none of the above` option. Note that the vendor does not publish the numbers behind that claim, so
  treat it as vendor guidance rather than a measured result.
- **An `other` or `none of the above` option, which remains acceptable.** It keeps the request to one
  question and the answer set closed, and it is the only option on a route where the caller wants a
  single decision per item. Accept the probability cost and measure it: the option is a real
  competitor, not a free label.

The offline checker warns with `NO_FALLBACK_OPTION` when a System One dialect Choice has neither a
companion question nor a `none`, `other`, or `unknown` option. That is a heuristic, not an API rule,
and it does not know about the companion question, so a request that uses one still gets the
warning. Say so in the handover rather than adding a dead option to silence it.

Source: <https://docs.typesafe.ai/primitives.md>,
<https://docs.typesafe.ai/patterns/companion-noul.md>, and the vendor guidance at
<https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## Score levels as situations

A Score returns a probability-weighted position along ordered levels, and the position can land
between two levels. Write each level as a situation a person could point at, not as an intensity
word. "Very angry" means something different to every reader; "uses strong language and repeats the
complaint" does not. Give each level a description and, where it helps, example situations, and
always define the low end so the middle of the scale has somewhere to sit.

Levels are weak for recovering an exact number. An in-between score is possible, but the number is
not a precise measurement of the underlying value: the vendor states that its score levels are weak
in numerical calibration and that the model cannot reconstruct the exact number by interpolating
between the two nearest levels. Use a Score to clear a threshold or to sort, never to reconstruct a
quantity.

Level counts differ by route. The System One dialect accepts one to ten levels and warns above ten;
b.ai requires at least two; the OpenAI dialect requires two to ten; the AI SDK accepts one, with a
portability warning, because a single level collapses every answer to the same score.

Source: <https://docs.typesafe.ai/primitives/score.md> and
<https://docs.typesafe.ai/model-jaggedness.md>.

## Boolean true and false descriptions

`criteria` is optional for a boolean question. When you write it, the only allowed keys are `true`
and `false`, and each holds a string, an object, or an array describing what that side means in your
domain. Treat the criteria as an extension of the instruction and align the wording of the two. A
question whose `true` side reads like a no is a known failure mode.

A boolean returns the probability that the answer is yes, and nothing else. A value near 0.5 means
the model gives yes and no equal weight, which is uncertainty rather than a medium-strength answer.
When you need a degree instead of a yes/no, use a Score with defined levels.

Source: <https://docs.typesafe.ai/primitives/noul.md>.

## Box questions

A Box returns four edges as fractions of the image height and width, and it has no null result:
there is no "not found" answer, so a question about something absent still returns four edges. Pair
every Box with a companion boolean that asks whether the object is visible, and gate the coordinates
on that answer.

Box needs an image in the request, a Jev 1.14 model, and the vendor's images header, and the vendor
marks images and Box as not ready for production. Do not ship a Box-dependent path without saying so.
The model ids, limits, and header names behind that are in
[`./official/jev-platform.md`](./official/jev-platform.md).

Source: <https://docs.typesafe.ai/primitives/box.md> and <https://docs.typesafe.ai/images.md>.

## Option order is a measurable bias

The order of a Choice's options can change the answer, and the vendor observed its own model leaning
toward the option that comes first. Its prescribed test is to reorder the options and check that the
answer stays consistent. The same test applies to a Choice whose options are labels rather than
descriptions: reordering is cheap, and a flip means the question is deciding on position rather than
content. Put the check in the evaluation plan rather than running it once by hand.

Source: <https://docs.typesafe.ai/model-jaggedness.md>.

## Refusals are not low probabilities

The OpenAI dialect has a fourth answer type per question, and a refusal is not the same as a
predicate answered with a low probability. Do not turn a refusal into `probability: 0`, the first
choice, or a zero score: give it its own branch, and treat it as a request that was declined rather
than as an answer. The AI SDK surfaces the same condition as a thrown refusal error, so code that
only reads `probability` will crash instead of misreading.

Source: <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> and
<https://ai-sdk.dev/docs/ai-sdk-core/decisions>.

## Encoding the state

The state is one value, and each dialect carries it differently.

| Dialect | How the state travels | Practical rule |
| --- | --- | --- |
| System One | `state` is a string, a JSON object, or an array; images go in `state`, `instructions`, or `criteria` through an `assets` map keyed by a placeholder | Send a JSON object when the question names paths; use placeholders and the images header only when an image is genuinely part of the judgment |
| OpenAI Decisions | `input` is a string, an array of input items (messages, tool records), or a JSON object passed as `input_json` | `input_json` is the structured path; it carries limits of its own, so keep nesting shallow and send only the fields the questions read |
| AI SDK | `state` is a string, a JSON object, or an array of content parts | A bare JSON array is read as content parts, so wrap records in an object |

Independently of the dialect: keep a JSON object under 64 nesting levels, send finite numbers only,
and send the state in the language it arrived in. Translating the content under judgment changes the
evidence being judged.

Source: <https://docs.typesafe.ai/concepts/state.md>,
<https://developers.openai.com/api/reference/resources/decisions/methods/create.md>, and
<https://ai-sdk.dev/docs/ai-sdk-core/decisions>.

## Candidate extraction

The model does not generate text well and does not count reliably. Both jobs go to code. The
extraction pattern keeps the model on the part it does well:

1. Code enumerates candidates for the value you want, with a regular expression, a parser, or a
   generative model that proposes options.
2. The decision model picks among the candidates with a Choice question whose options are the
   candidates.
3. Code copies the chosen value verbatim from the candidate list and normalizes it.

The vendor recommends exactly this split: extract candidate options with code or a generative model,
and let the decision model pick the correct one.

Measure the two halves apart, because they fail for different reasons:

- **Candidate coverage**: does the true value appear among the candidates at all? A low number here
  is a code problem in the enumerator, and no question wording will fix it.
- **Selection accuracy**: given the true value was among the candidates, did the model pick it? A low
  number here is a question problem, usually options that are hard to tell apart.

A single end-to-end accuracy number hides which half is broken. Report both, and fix the failing
half.

Source: <https://docs.typesafe.ai/model-jaggedness.md> and
<https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## Korean input

Write instructions in English by default. The vendor describes English as its best-supported
language, and while the current model line advertises better multilingual support than the previous
one, no public measurement of that improvement exists in the pages captured here.

Keep the state in the language it arrived in, and treat Korean input as unproven until you have
tested it:

1. Run a pilot over your own Korean content, with labels you trust.
2. Compare the answers against those labels and record where they disagree.
3. Keep a confidence gate that sends low-confidence answers to a person, and widen the review band
   while the evidence is thin.
4. Pin a versioned model id once thresholds are tuned, so a silent alias move cannot change them.

One decision vendor markets Korean strength specifically, at beta status, and its request contract
is not documented in a first-party specification this package could open. Treat a vendor language
claim as a hypothesis to test, not as a reason to skip the pilot.

Source: <https://docs.typesafe.ai/changelog.md>, <https://docs.typesafe.ai/models.md>, and
<https://arxiv.org/abs/2609.37647>.

## Documented weak spots

The vendor lists nine failure modes for its own model and a workaround for each. The design
consequence is the same throughout: give the model the judgment, keep the computation in code. The
page is no longer version-scoped, so read it against the model you actually use, and treat any
threshold you calibrate from an example there as fitted to whichever version produced that example.

| Failure mode | Workaround in the question design |
| --- | --- |
| Literal reading: the answer follows the words, not the intent | Write the exact condition in `instructions` and put boundary cases in the criteria |
| Math and numbers: counting and numeric representations are unreliable | Count and compute in code; send names or buckets instead of hex or binary values |
| Date and time comparison: dates are read as text, not as ordered quantities | Extract each date part with a Choice over a closed set, then compare in code |
| Indirection: double negatives and multi-hop questions lose accuracy | Cut the hops and name the relevant state paths directly |
| Large state full of irrelevant detail: unrelated content distracts | Filter in code and send only the fields the question needs |
| Adversarial content: state is data and is not treated as hostile | Write precise criteria and test the edge cases before shipping wide |
| Contradictory instructions and criteria: the two can fight | Align the criteria with the instruction and read both aloud |
| Choice option order: the first option attracts the answer | Reorder the options and check that the answer stays consistent |
| Generation: the model is not trained to produce text | Use the extraction pattern above, with code owning the text |

Source: <https://docs.typesafe.ai/model-jaggedness.md>.

## Request validity checklist

Run this list by hand when the offline checker cannot run, for example where bash or jq is not
installed or the checker has been removed. It mirrors the checks in
`../scripts/check-decision-request.sh` and the error codes that script prints. The script takes
`--route systemone`, `--route openai`, `--route aisdk`, or `--route bai`, and defaults to
`systemone`.

The checks come in five groups: what every route shares, what the container requires, what a question
entry requires, what the criteria require, and the image assets one route may carry. Read the group
that matches the route in play.

**Every route**

1. The file is valid JSON. Otherwise `INVALID_JSON`, or `INPUT_TOO_DEEP` when the document nests
   deeper than the checker's parser can read.
2. The root is a JSON object, not an array or a scalar. Otherwise `ROOT_NOT_OBJECT`.
3. No string value in the document looks like a credential; object keys are not scanned, and the
   value itself is never echoed. Otherwise `SECRET_IN_REQUEST`.

**The container**

4. `systemone`: `state` is present and is a string, an object, or an array, and `model` is a non-empty
   string. Otherwise `STATE_MISSING`, `STATE_TYPE`, or `MODEL_MISSING`. `questions` is a non-empty
   object. Otherwise `QUESTIONS_MISSING` or `QUESTIONS_EMPTY`.
5. `bai`: the same, plus `model` must be exactly `jev-1.13.0` or `jev-latest` (`MODEL_UNSUPPORTED`),
   `stream` must be absent or `false` (`STREAM_NOT_SUPPORTED`), and `assets` must be absent
   (`ASSETS_NOT_SUPPORTED`).
6. `aisdk`: `state` is present and typed as above, and `questions` is a non-empty object. There is no
   `model` field; a top-level `model` is an unknown field.
7. `openai`: `input` is present and is a string or a non-empty array. An absent field is
   `INPUT_MISSING`, an empty or whitespace-only string and an empty array are `INPUT_EMPTY`, and any
   other type is `INPUT_TYPE`. `model` is a non-empty string, and `questions` is an array of one to 400
   entries (`QUESTIONS_MISSING` when it is not an array, `QUESTIONS_EMPTY` when it is empty,
   `QUESTIONS_COUNT` above 400).

**A question entry**

8. `systemone` and `bai`: each entry is an object (`QUESTION_NOT_OBJECT`), its id is not blank
   (`QUESTION_ID_BLANK`), `type` is one of `noul`, `choice`, `score`, plus `box` on `systemone` only
   (`QUESTION_TYPE`), and `instructions` is present and is a string, an object, or an array
   (`INSTRUCTIONS_MISSING`, `INSTRUCTIONS_TYPE`).
9. `aisdk`: the same, with `type` one of `boolean`, `choice`, `score`, `box`.
10. `openai`: each entry is an object, `type` is one of `predicate`, `choice`, `score`
    (`QUESTION_TYPE`), `name` is a non-empty string and unique across the request
    (`QUESTION_NAME_MISSING`, `QUESTION_NAME_TYPE`, `QUESTION_NAME_DUPLICATE`), and there is no
    `criteria` field (`CRITERIA_NOT_SUPPORTED`).

**Criteria, by question type**

11. Boolean (`noul` or `boolean`): criteria is optional; when present each key is `true` or `false`,
    either key may be omitted, and each present value is a string, an object, or an array. Otherwise
    `NOUL_CRITERIA_TYPE`, `NOUL_CRITERIA_KEY`, `NOUL_CRITERIA_VALUE`, or the `BOOLEAN_` names on the
    AI SDK route.
12. `choice` on `systemone`, `bai`, and `aisdk`: criteria is a required object with 1 to 255 options,
    and each option description is `null`, a string, an object, or an array. Otherwise
    `CHOICE_CRITERIA_MISSING`, `CHOICE_CRITERIA_COUNT`, or `CHOICE_CRITERIA_VALUE`.
13. `choice` on `openai`: `choices` is a required array of 2 to 255 entries; each entry is an object
    with a `value` that is a string or a boolean and an optional description; values must be unique.
    Otherwise `CHOICE_CHOICES_MISSING`, `CHOICE_CHOICES_COUNT`, `CHOICE_NOT_OBJECT`,
    `CHOICE_VALUE_MISSING`, `CHOICE_VALUE_TYPE`, `CHOICE_DESCRIPTION_TYPE`, or
    `CHOICE_VALUE_DUPLICATE`.
14. `score` on `systemone` and `aisdk`: criteria is a required array of 1 to 10 items, each a string,
    an object, or an array and never `null`. Otherwise `SCORE_CRITERIA_MISSING`,
    `SCORE_CRITERIA_COUNT`, or `SCORE_LEVEL_TYPE`. A single level raises `SCORE_LEVELS_SINGLE` on
    `systemone` and `SCORE_LEVELS_PORTABILITY` on `aisdk`, both as warnings.
15. `score` on `bai`: the same, with 2 to 10 items, so a single level is `SCORE_CRITERIA_COUNT`.
16. `score` on `openai`: `levels` is a required array of 2 to 10 objects, each with a string `label`
    and an optional description. Otherwise `SCORE_LEVELS_MISSING`, `SCORE_LEVELS_COUNT`,
    `SCORE_LEVEL_NOT_OBJECT`, `SCORE_LABEL_MISSING`, `SCORE_LABEL_TYPE`, or
    `SCORE_DESCRIPTION_TYPE`.
17. `box`: no criteria at all (`BOX_CRITERIA_UNSUPPORTED`). `systemone` also warns
    `BOX_REQUIREMENTS` because alignment, model version, and the images header are outside the
    document; `aisdk` warns `BOX_PROVIDER_PORTABILITY` because only one provider implements it.

**Assets, on the routes that carry them**

18. `systemone` only: `assets` is a non-empty object (`ASSETS_TYPE`), each asset is an object
    (`ASSET_NOT_OBJECT`), a `type` other than `image` is `ASSET_TYPE`, and an asset carrying
    `data_base64` needs `format` to be `png`, `jpg`, or `jpeg` (`ASSET_FORMAT`). An asset that no
    string in the state or the questions refers to raises `ASSET_UNREFERENCED` as a warning.

**Warnings the checker raises without failing the request:** `UNKNOWN_TOP_LEVEL_FIELD` for a
top-level key outside the route's allowed set; `NO_FALLBACK_OPTION` for a Choice with no `none`,
`other`, or `unknown` option; `INPUT_LARGE` when a length-divided-by-four estimate puts the input
plus the longest question over the 32,000-token limit; `INPUT_TOO_LONG` on `openai` for a string
`input` past the documented character ceiling; `MODEL_UNVERIFIED` on `openai` for a model other than
`gpt-6-luna`; and the score and box warnings listed above.

**Exit codes.** 0 when there are no errors, 1 when there is at least one error including an
unparsable file or a document nested past the checker's depth limit, and 2 for a usage problem (no
file argument, an unreadable file, or an unknown route). Run it from the skill folder as:

```bash
bash scripts/check-decision-request.sh --route openai path/to/request.json
```

Treat a green run as a check on shape only. A well-formed request can still be a bad question, and
which of those two you have shows up only against labeled data.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| A question id was documented as not sent to the model on the captured API page | <https://docs.typesafe.ai/api/system-one.md> |
| The question map and its `minProperties: 1`, and `instructions` accepting a string, an object, or an array | <https://docs.typesafe.ai/api/system-one.md> and <https://docs.typesafe.ai/primitives/advanced.md> |
| Structured instructions, contrastive Choice criteria, and state paths in backticks | <https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md> |
| Up to 255 Choice options and the cost of each added option | <https://docs.typesafe.ai/primitives/choice.md> |
| The four primitives, the companion boolean over an `other` option, and the meaning of 0.5 on a boolean | <https://docs.typesafe.ai/primitives.md> |
| The Box contract, the missing not-found answer, and the production warning | <https://docs.typesafe.ai/primitives/box.md> and <https://docs.typesafe.ai/images.md> |
| Scores, their level counts, and weak numerical calibration | <https://docs.typesafe.ai/primitives/score.md> and <https://docs.typesafe.ai/model-jaggedness.md> |
| The nine documented weak spots and the option-order bias | <https://docs.typesafe.ai/model-jaggedness.md> |
| The state types per dialect, the images path, and the request rules on nesting and numbers | <https://docs.typesafe.ai/concepts/state.md>, <https://docs.typesafe.ai/api/errors.md>, <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| `predicate`, `choices`, `levels`, `input`, `input_json`, the required `name`, and the refusal answer | <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> and <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| The `boolean`, `choice`, `score`, `box` names, the missing distributions on the language-model adapters, and the thrown refusal | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> |
| The human test, decisions as a truth table, and the wrong-layer question | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| Better multilingual support in the current model line, and English as the best-supported language | <https://docs.typesafe.ai/changelog.md> and <https://docs.typesafe.ai/models.md> |
| The multilingual accuracy gradient behind the Korean pilot rule | <https://arxiv.org/abs/2609.37647> |
| A decision vendor marketing Korean strength at beta status | <https://developers.upstage.ai/docs/models/solar-decide.md> |
| The checker's routes, codes, and exit codes | `../scripts/check-decision-request.sh` |

### Evidence grade

`PRIMARY` for the design rules above: each traces to a vendor page captured on 2026-11-08, except the
id-visibility sentence, which is a vendor statement from the 2026-10-01 capture of that page and is
labelled as such. `PRIMARY` for the checker row, read from the script in this package rather than
from a description of it. `SECONDARY` for the multilingual gradient, which comes from one independent
preprint. `LOCAL` for the recommendation to prefer a companion boolean, which is this package's
default on top of the vendor's guidance, and for the structure of the checklist, which groups the
script's checks rather than adding rules of its own.

Not evidenced here and deliberately left unspecified: prices, request limits, model ids, endpoints,
and the per-route contract differences. Those live in [`./providers.md`](./providers.md) and the
snapshots under [`./official/`](./official/).
