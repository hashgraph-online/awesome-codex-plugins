# Mode Procedures

Seven modes cover everything this skill produces: `design`, `questions`, `code`, `template`, `eval`,
`audit`, and `provider`. Each block below carries the signals that pick the mode, the inputs it needs
with the defaults that fill the gaps, the steps in order, the files it writes and where they go, how
the result is verified, and the condition that ends the run.

The mode is read from the artifact the user wants to open, using the table in
[`../rules/modes-and-routing.md`](../rules/modes-and-routing.md). The fit gate in that file runs
before any mode below: a `code` or `llm` verdict stops the work there, a `hybrid` or `decompose`
verdict splits the request first and continues on the decision-model part alone, `provider` and any
request whose deliverable is an action rather than a judgment skip the gate, and `audit` runs the gate
once per candidate call. Route facts come from [`./providers.md`](./providers.md) and the snapshots
under [`./official/`](./official/); prices, limits, endpoints, and model ids are not restated in this
file because they move.

## Contents

- Shared rules
- design
- questions
- code
- template
- eval
- audit
- provider
- Sources

## Shared rules

**Where artifacts go.** Write to the path the user gave, when they gave one. Otherwise write under
`.hyper/decision/<topic>/`, where `<topic>` is a short slug taken from the request. Report every path
written.

**Never overwrite without confirmation.** Read an existing file first, then either write a sibling
file or ask before replacing it. This holds for every mode, including `template` and `code`, where the
destination is the most likely to already exist.

**Two ways to verify a request.** The offline checker at `../scripts/check-decision-request.sh` is the
default, and it needs bash 3.2 or newer with jq. Its `--route` value is `systemone`, `openai`,
`aisdk`, or `bai`, and it defaults to `systemone`. When bash or jq is not available, run the request
validity checklist in [`./question-design.md`](./question-design.md) by hand instead, and say in the
handoff that the check was manual.

**The route tier decides what a caller may assume.** A `T1` or `T2` route returns a typed answer with
a distribution, so a threshold is meaningful. A `T3` route is emulation on a general model and returns
a label with no distribution, so a generated caller gets a review path instead of a threshold and says
so in a comment. A `T4` route is not a decision route and gets no caller at all.

**Stopping.** A mode stops when its artifact exists, its verification has run, and its own stop
condition below holds. The fit gate, a missing input only the user can supply, and an unverified route
stop the work earlier.

## design

**Signals.** "Should this use a decision model", "is this a judgment problem", "decision model or
code", "how should I split this", "decision contract". Korean: "결정 모델로 하는 게 맞나", "판단
문제인가", "어떻게 나눌까", "결정 계약".

**Required inputs and defaults.** The description of the feature, and the outputs it has to produce.
No repository file is required, but read the surrounding code when a path is given. Default language
and route come from [`../rules/modes-and-routing.md`](../rules/modes-and-routing.md).

**Steps.**

1. Run the fit gate. Record the verdict and the question that decided it.
2. If the verdict is `code` or `llm`, write the split or the alternative without a decision artifact:
   name the part code owns, the part a generative model owns, and the part a decision model would own
   if the request is decomposed.
3. If the verdict is `decision`, `decompose`, or `hybrid`, write the decision contract: one row per
   decision, with the judgment it asks for, the type of answer it takes, who acts on the answer, and
   what happens when the probability is low. For `hybrid`, write the split first and then write the
   contract for the decision-model half only. For `decompose`, move the arithmetic and the policy to
   code, write the contract for the judgment part only, and re-check that part against the gate.
4. Write the decision itself as a table in code, as the vendor guidance puts it. The contract lists
   the judgments the decision reads; the decision is a truth table over them, and each row names the
   action. A combination with no defined outcome is a design gap, so mark it rather than widening a
   question to cover it.
5. Name the fields of the state each question reads, and apply the human test to that state: could a
   capable person, shown only this state and this question, answer quickly. Note the fields you had to
   add to make that true.
6. Mark every part that still needs a person's decision instead of guessing it.

**Output files and location.** `decision-contract.md` under the default location, or the path the user
gave.

**Verification.** Re-read the contract against the gate: every row must ask one judgment over text or
an image, and no row may ask for arithmetic, counting, date comparison, or generated prose. No row may
ask the model to make the decision itself. If the contract cannot pass the gate again, the split is
wrong and is rewritten.

**Stop when** the contract lists every decision, each row passes the gate, the state passes the human
test, and the review path for a low probability is stated. Nothing is called and no request file is
written.

## questions

**Signals.** "Write the questions", "question set", "criteria", "options", "scale", "make the labels".
Korean: "질문 만들어", "질문 묶음", "선택지", "점수 단계".

**Required inputs and defaults.** The decision from `design`, or a description of it. The language of
the instructions defaults to English; the state keeps whatever language the user's data is in. Per
question, choose from the neutral types by the shape of the answer, per
[`./question-design.md`](./question-design.md), then spell them the way the route in play spells them:
`noul`/`choice`/`score`/`box` on the System One dialect, `predicate`/`choice`/`score` on the OpenAI
dialect, `boolean`/`choice`/`score`/`box` on the AI SDK.

**Steps.**

1. Write one question per judgment. Split anything that hides two judgments behind one answer.
2. Give each question a type and an instruction that states the condition in full, since the meaning
   has to live in the instruction rather than in an id.
3. For `choice`, write the option list and describe each option with what it covers, what belongs to
   a neighbour, and examples. For `score`, describe each level with a situation. For a boolean,
   describe what `true` and `false` each mean.
4. Decide how "none of these" leaves the request: a companion boolean by default, an `other` or
   `none` option where a single closed answer set is required. Note which one you chose and why.
5. Point at state fields by name in backticks, using the field names settled in `design`.
6. Assemble the questions into a request file for the route in play, with a sample state so it can be
   checked.
7. Run the offline checker on the assembled file with that route's `--route` value. When bash or jq is
   unavailable, run the checklist in [`./question-design.md`](./question-design.md) by hand and say so.
8. Write `questions.md`: the choice behind each question, the fallback decision, the model id and the
   snapshot date it came from, and the note to re-check the snapshot before the first live call.

**Output files and location.** `request.json` plus a short `questions.md` explaining the choices, under
the default location or the path the user gave. The request JSON carries no comment, so the snapshot
date, the model id, and the note to re-check before the first live call go into `questions.md`.

**Verification.** The checker report must carry no errors for the chosen route, or the manual checklist
must clear every line. A question whose answer cannot be acted on directly in code is rewritten before
the artifact is handed over. A `NO_FALLBACK_OPTION` warning that comes from a deliberate companion
question is recorded in `questions.md` rather than silenced with a dead option.

**Stop when** each question is atomic, its answer type matches what the code will do with the answer,
and the request passes the check for its route.

## code

**Signals.** "Call it from", "integration code", "client", "wire this into", "TypeScript", "Python".
Korean: "호출 코드", "연결 코드", "연동".

**Required inputs and defaults.** Questions and thresholds if they exist, otherwise a question set from
the `questions` mode. Language defaults to TypeScript; `pyproject.toml` means Python only when
`package.json` is absent, so when both files exist the language is TypeScript. Route and tier follow
the order in [`./providers.md`](./providers.md). Read the contract values from the snapshots under
[`./official/`](./official/) rather than writing them into the code, with the one exception of the
named endpoint and model constants described in
[`../rules/safety-and-boundaries.md`](../rules/safety-and-boundaries.md) section 9.

**Steps, in this order.**

1. **Fit gate.** Run the five questions before writing anything. Only `decision` and `decompose`
   continue; a `code` verdict answers the request with plain code and no caller, an `llm` verdict keeps
   the model that already writes the text, and `hybrid` is split first. State the verdict in one line.
2. **Route, tier, and language decision.** Pick the route from the order in
   [`./providers.md`](./providers.md) and the language from the repository. Say which route, which
   tier, and which language were chosen, because the question type names, the input key, and the
   probability path all change with the dialect.
3. **Constants file first.** Write the file holding the questions, the model id, and the thresholds
   before the caller. Thresholds carry a comment marking them as untuned assumptions until the user's
   own data says otherwise. On a `T3` route there are no thresholds: the file holds a review-path flag
   and a comment saying the route returns no distribution.
4. **Call file.** Write the single caller for the chosen route and language: read the key from the
   environment by name at call time, send one state with all questions in one request, and never print,
   log, or write the key. Pin a versioned model id rather than an alias, and record the model id the
   response reports.
5. **Request check with the offline checker.** Assemble the same questions into a request file and run
   `bash scripts/check-decision-request.sh --route <route> <file>`, run from the skill folder, where
   `--route` is one of `systemone`, `openai`, `aisdk`, or `bai`. Exit 0 is required before the caller
   is handed over; exit 1 names the field to fix. When bash or jq is unavailable, run the checklist in
   [`./question-design.md`](./question-design.md) by hand and say so.
6. **Response validation.** The caller checks every answer before acting on it: every question sent is
   present in the response, the answer type matches the question type sent, a choice answer is one of
   the options sent, a score answer falls inside the level range, a probability falls between 0 and 1,
   and a distribution sums to 1 inside a small tolerance. A refusal is its own branch and is never
   coerced into a probability, the first option, or a zero score. A response that fails any of these
   is an error, not a value to coerce.
7. **Probability-gated branch.** Route by the probability of the action, not by `confidence`. A
   boolean answer is branched on its probability; a choice or score answer is branched on the
   probability of the option or the cumulative probability of the levels on the acting side. The low
   band returns a review path that sends the item to a person, and the band boundary is a named
   constant from step 3 rather than a literal in the caller. On a `T3` route there is no probability
   to branch on, so this step becomes the review path chosen in step 3 and the caller says so in a
   comment instead of pretending to threshold a label.
8. **Consent before any live call.** The generated code does not call the service on its own. Before
   the first live request, ask the person, say what the call will cost using the snapshot under
   [`./official/`](./official/), and keep the run to the smallest number of requests that answers the
   question. A key in the environment, or the checker passing, is not consent.
9. **Stop.** Hand over the files, the checker result, and the route, tier, and language decisions. Do
   not run a live call inside this mode.

**Output files and location.** `constants.ts` (or `constants.py`), the caller file, and the
`request.json` that step 5 assembles, under the default location or the path the user gave. The
constants file and `request.json` carry the same model id and must be kept in step. Report all three
paths and the checker exit code.

**Verification.** The checker exits 0 for the route, or the manual checklist cleared every line when
bash or jq is unavailable; the caller compiles in the target language, and the response validation
from step 6 is present in the file rather than promised in a comment.

**Stop when** the constants file and the caller exist, the checker passed for the route in play, and
the live call is left to the user with the consent step stated.

## template

**Signals.** "Request json", "constants file", "routing table", "starter", "skeleton", "boilerplate".
Korean: "요청 JSON", "상수 파일", "라우팅 표", "템플릿", "뼈대".

**Required inputs and defaults.** The decision and the state fields. Everything else has a default, and
the point of this mode is to leave the defaults visible so the user edits them.

**Steps.**

1. Write `request.json` in the System One dialect and `request-openai.json` in the OpenAI dialect from
   the same question set, so the pair shows the dialect difference on one example. Each carries a
   sample state, one boolean question, one `choice`, one `score`, and a model field that the snapshot
   lists as accepted for that dialect.
2. Write the constants file with the questions, the model ids, and the thresholds exported together,
   thresholds marked as untuned assumptions.
3. Write the routing table mapping each answer to the code path that acts on it, including the low
   probability row and the refusal row.
4. Run the checker on each request file for its route: `--route systemone` for `request.json` and
   `--route openai` for `request-openai.json`. A template written for the SDK route is checked with
   `--route aisdk`.
5. Put the replace-before-call note in the constants file header and in the report; a JSON file gets
   none, because a note key would come back as an unknown field from the checker.

**Output files and location.** `request.json`, `request-openai.json`, `constants.ts`, and
`routing-table.json` under the default location or the path the user gave.

**Verification.** The checker exits 0 for every route the template claims, and the routing table has a
row for every answer the questions can produce, plus the refusal row.

**Stop when** the files exist, every claimed route passes the check, and the replace-before-call note
is present in the constants header and the report.

## eval

**Signals.** "Evaluate", "test set", "labels", "thresholds", "how accurate", "before we ship". Korean:
"평가", "라벨", "임계값", "정확도", "검증 세트".

**Required inputs and defaults.** The decision being made, the questions, the route and its tier, and
as many labeled examples as the user has. With no labels, the plan says where they come from and treats
the first batch as provisional. On a `T3` route the plan carries no threshold tuning, because there is
no distribution to threshold.

**Steps.**

1. Write the decision down and price each error type: a false positive and a false negative rarely cost
   the same, and the threshold follows the cost rather than the accuracy.
2. Build the case set: representative cases, then the hard ones. The hard list starts with negation,
   quoted third-party text, two intents in one message, missing information whose expected label is
   null, an instruction embedded inside the state, a statement that fits no listed option, reversed
   label polarity, and informal Korean.
3. Split the cases into a threshold-tuning split and a reported eval split, and keep the two apart.
   Group near-duplicates before splitting, and stratify on the classes and the slices that decide the
   deployment.
4. Pin the model version for any comparison whose result must hold still, and record the model id the
   response reports rather than the alias in the request. See [`./eval-and-audit.md`](./eval-and-audit.md)
   for the reasoning.
5. Tune thresholds on the tuning split, starting from the bands by question shape, then report on the
   eval split. Draw the review band from the cost of each error, not from the accuracy curve alone.
   On a `T3` route, set the review path instead and skip this step.
6. Add the label-free checks: repeat every case and report the flip rate, and run the option-order and
   polarity permutations.
7. Add the calibration check per question shape, and report an interval beside every rate.
8. Name the baselines the result is compared against, including the current rule or regex where one
   exists, and the other routes when the question is which route to use.
9. Review every change to the question set against the prompt-gymnastics list, and propose the
   structural fix where a change reads as gymnastics.
10. Before any live measurement, the safety rules apply: the person's consent for the call, separate
    consent when the state carries private data, and one request first, in the smallest useful shape.
    State the estimated cost from the snapshot under [`./official/`](./official/), counting the
    repetitions.

**Output files and location.** `eval-plan.md` and `eval-cases.jsonl` under the default location or the
path the user gave. Case rows carry the expected label, including a null label where the honest answer
is "not enough information", and the split each row belongs to.

**Verification.** The plan names the tuning split, the reported split, the measurement that decides each
threshold, the repeat and permutation checks, and the calibration check per question shape. The case
rows carry their expected labels including the null rows.

**Stop when** the plan defines both error costs, the two splits are separate, the tuning procedure and
the label-free checks are written, and every change to the question set has been reviewed against the
prompt-gymnastics list. This mode produces the plan, the case template, and the tuning procedure; it
does not run the live measurement itself.

## audit

**Signals.** "Audit", "find the LLM calls", "what should we replace", "where do we waste calls". Korean:
"감사", "LLM 호출 찾아", "교체 대상", "어디서 낭비하나".

**Required inputs and defaults.** A repository path and, if the user has one, the list of files they
care about. Default scope is the whole working tree minus dependencies and generated code.

**Steps.**

1. Find every place a model is called and only a label comes back: the answer set is finite, the caller
   parses the reply into one of those values, no person reads the reasoning, and the call runs often or
   a person waits on it. Include the shapes that hide the pattern: a structured-output enum, a
   `logit_bias` table, a logprob read turned into a confidence, a moderation call used as a classifier,
   and a deprecated judge or grader used at runtime.
2. Disqualify the calls a decision model cannot serve, using the documented limits: anything needing
   arithmetic, counting, date comparison, multi-hop reasoning, or generated text stays where it is. A
   call whose label must be exactly right and cannot be verified stays too.
3. Measure each remaining call: calls per day, p50 and p95 latency, tokens per call split by direction,
   and what is blocked while it runs.
4. Rank by what the swap would save, how cleanly the label maps onto a question type, and whether the
   target tier keeps a distribution.
5. Write the table, including the target route tier and the expected probability source, then stop.

**Output files and location.** A single report, `audit.md`, written under `.hyper/decision/<topic>/`
outside the tree being audited, or given in the reply, or at the path the user gave when that path is
outside the audited tree. Nothing else is written.

**Verification.** Every row cites a file and line, every row names a tier and a probability source, the
report was produced without editing any file in the audited tree, and the report itself sits outside
that tree.

**Stop when** the table is written and the working tree is unchanged. This mode is read-only: it finds
candidates and never rewrites them.

## provider

**Signals.** "Which provider", "which route", "connect it", "setup", "environment", "tier". Korean:
"어느 경로", "어디로 연결", "설정", "환경 변수".

**Required inputs and defaults.** The repository, and the name of the key the user already has, checked
by name only.

**Steps.**

1. Pick the tier first, then the route. Use a `T1` native endpoint when the answer needs a
   distribution, a `T2` SDK or gateway when the project already depends on that SDK or needs one
   interface over several vendors, and a `T3` emulation only when a `T1` or `T2` route is unavailable
   and a label without a distribution is acceptable. A `T4` route is not an option here; it goes to
   `audit` or `design` instead.
2. Take the order inside the chosen tier from [`./providers.md`](./providers.md), starting from what
   the repository already depends on.
3. Check which environment variable names exist, never their values, and report the answer as a name.
4. Write the setup steps for the chosen route alone, including where the key is read, what must not be
   logged, and the model id to pin. The setup document names the environment variable, the route, and
   the tier, and points at [`./providers.md`](./providers.md) and the matching snapshot under
   [`./official/`](./official/) for the accepted ids and the endpoint; it does not copy them into
   prose, because they are refreshed in those files.
5. If the user named a route that carries no verified contract, say so and produce no code for it.
6. State the first-call rule: one live request, after consent, with the cost named first.

**Output files and location.** `provider-setup.md` under the default location or the path the user
gave.

**Verification.** The chosen route and tier have a verified row in [`./providers.md`](./providers.md),
the environment variable is named rather than valued, the model id is pinned rather than aliased, and
no key value appears in the document.

**Stop when** the setup document names the tier, the route, the environment variable, the pinned model
id, and the first-call rule, and no live call was made.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
| --- | --- |
| The mode set, the per-mode signals, and the fit gate that runs first | [`../rules/modes-and-routing.md`](../rules/modes-and-routing.md) |
| The shape of a question, the criteria and companion-question guidance, and the manual checklist used when bash or jq is missing | [`./question-design.md`](./question-design.md) |
| The route tiers, the route order, the key handling rule, and the routes that carry no verified contract | [`./providers.md`](./providers.md) |
| The output path default and the no-overwrite rule | repository policy |
| The question types, the answer fields validated after a call, and their names per dialect | <https://docs.typesafe.ai/api/system-one.md> and <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| The boolean, choice, score, and box names on the SDK contract, and the missing distributions on a language-model route | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> |
| The documented limits that disqualify a call, and the option-order test | <https://docs.typesafe.ai/model-jaggedness.md> |
| Probability-first routing, the starting band, and the cumulative-probability fix for a split answer | <https://docs.typesafe.ai/confidence.md> and <https://docs.typesafe.ai/patterns/confidence-routing.md> |
| The human test for the state, decisions as a truth table in code, and the prompt-gymnastics list | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| The single-constants-file habit and the warning that a stale copy makes an agent invent fields | <https://docs.typesafe.ai/models.md> |
| The checker's routes, flags, and exit codes | `../scripts/check-decision-request.sh` |

### Evidence grade

`LOCAL` for the shared rules, the per-mode steps, and the stop conditions: they are this package's
procedure built on the repository's own routing and question guidance. `VENDOR` for the question
shapes, the answer fields, the documented limits, the probability guidance, and the audit signals, each
carried by the linked page. `PRIMARY` for the checker row, which was read from the file in this package
rather than from a description of it.

Prices, rate limits, context budgets, endpoint names, and model ids are deliberately absent here. They
live in [`./providers.md`](./providers.md) and the snapshots under [`./official/`](./official/), behind
a review date.
