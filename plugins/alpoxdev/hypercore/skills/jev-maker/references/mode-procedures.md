# Mode Procedures

Seven modes cover everything this skill produces: `design`, `questions`, `code`, `template`, `eval`,
`audit`, and `provider`. Each block below carries the signals that pick the mode, the inputs it needs
with the defaults that fill the gaps, the steps in order, the files it writes and where they go, how
the result is verified, and the condition that ends the run.

The mode is read from the artifact the user wants to open, using the table in
[`../rules/modes-and-routing.md`](../rules/modes-and-routing.md). The fit gate in that file runs
before any mode below: a `code` or `llm` verdict stops the work there, a `hybrid` or `decompose`
verdict splits the request first and continues on the Jev-owned part alone, `provider` and any request
whose deliverable is an action rather than a judgment skip the gate, and `audit` runs the gate once per
candidate call. Route facts come from
[`./providers.md`](./providers.md) and [`./official/jev-platform.md`](./official/jev-platform.md);
prices, limits, endpoints, and model aliases are not restated in this file because they move.

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
`.hyper/jev-maker/<topic>/`, where `<topic>` is a short slug taken from the request. Report every
path written.

**Never overwrite without confirmation.** Read an existing file first, then either write a sibling
file or ask before replacing it. This holds for every mode, including `template` and `code`, where the
destination is the most likely to already exist.

**Two ways to verify a request.** The offline checker at `../scripts/check-jev-request.sh` is the
default, and it needs bash 3.2 or newer with jq. When bash or jq is not available, run the request
validity checklist in [`./question-design.md`](./question-design.md) by hand instead, and say in the
handoff that the check was manual.

**Stopping.** A mode stops when its artifact exists, its verification has run, and its own stop
condition below holds. The fit gate, a missing input only the user can supply, and an unverified route
stop the work earlier.

## design

**Signals.** "Should this use Jev", "is this a judgment problem", "Jev or code", "how should I split
this", "decision contract". Korean: "Jev로 하는 게 맞나", "판단 문제인가", "어떻게 나눌까".

**Required inputs and defaults.** The description of the feature, and the outputs it has to produce.
No repository file is required, but read the surrounding code when a path is given. Default language
and route come from [`../rules/modes-and-routing.md`](../rules/modes-and-routing.md).

**Steps.**

1. Run the fit gate. Record the verdict and the question that decided it.
2. If the verdict is `code` or `llm`, write the split or the alternative without a Jev artifact: name
   the part code owns, the part a generative model owns, and the part Jev would own if the request is
   decomposed.
3. If the verdict is `jev`, `decompose`, or `hybrid`, write the decision contract: one row per
   decision, with the question it asks, the type of answer it takes, who acts on the answer, and what
   happens when confidence is low. For `hybrid`, write the split first and then write the contract for
   the Jev half only. For `decompose`, move the arithmetic and the policy to code, write the contract
   for the Jev part only, and re-check that part against the gate.
4. Name the fields of the state each question reads, so the next mode has a fixed input shape.
5. Mark every part that still needs a person's decision instead of guessing it.

**Output files and location.** `decision-contract.md` under the default location, or the path the user
gave.

**Verification.** Re-read the contract against the gate: every row must ask one judgment over text, and
no row may ask for arithmetic, counting, date comparison, or generated prose. If the contract cannot
pass the gate again, the split is wrong and is rewritten.

**Stop when** the contract lists every decision, each row passes the gate, and the review path for low
confidence is stated. Nothing is called and no request file is written.

## questions

**Signals.** "Write the questions", "question set", "criteria", "options", "scale", "make the labels".
Korean: "질문 만들어", "질문 묶음", "선택지", "점수 단계".

**Required inputs and defaults.** The decision from `design`, or a description of it. The language of
the instructions defaults to English; the state keeps whatever language the user's data is in. Per
question, choose `choice`, `score`, or the yes/no type from the shape of the answer, per
[`./question-design.md`](./question-design.md). The yes/no type is `noul` on the direct and b.ai routes
and `boolean` on the AI SDK route.

**Steps.**

1. Write one question per judgment. Split anything that hides two judgments behind one answer.
2. Give each question a type and an instruction that states the condition in full, since the question
   id never reaches the model.
3. For `choice`, write the option list including a `none` option, and describe each option with `what`,
   `not_for`, and `examples`. For `score`, describe each level with a situation. For `noul`, describe
   what `true` and `false` each mean.
4. Point at state fields by name in backticks, using the field names settled in `design`.
5. Assemble the questions into a request file with a sample state so it can be checked.
6. Run the offline checker on the assembled file for the route in play. When bash or jq is
   unavailable, run the checklist in [`./question-design.md`](./question-design.md) by hand and say so.
7. Write `questions.md`: the choice behind each question, the source file the snapshot's values came
   from, and the snapshot date, with the note to re-check it before the first live call.

**Output files and location.** `request.json` plus a short `questions.md` explaining the choices, under
the default location or the path the user gave. The request JSON carries no comment, so the snapshot
date, the source file it came from, and the note to re-check before the first live call go into
`questions.md`.

**Verification.** The checker report must carry no errors for the chosen route, or the manual checklist
must clear every line. A question whose answer cannot be acted on directly in code is rewritten before
the artifact is handed over.

**Stop when** each question is atomic, its answer type matches what the code will do with the answer,
and the request passes the check for its route.

## code

**Signals.** "Call it from", "integration code", "client", "wire this into", "TypeScript", "Python".
Korean: "호출 코드", "연결 코드", "연동".

**Required inputs and defaults.** Questions and thresholds if they exist, otherwise a question set from
the `questions` mode. Language defaults to TypeScript; `pyproject.toml` means Python only when
`package.json` is absent, so when both files exist the language is TypeScript. Route follows
the order in [`./providers.md`](./providers.md). Read what is needed from
[`./official/jev-platform.md`](./official/jev-platform.md) rather than writing contract values into the
code. The one exception is the single named endpoint and model constants described in
[`../rules/safety-and-boundaries.md`](../rules/safety-and-boundaries.md) section 9.

**Steps, in this order.**

1. **Fit gate.** Run the five questions before writing anything. Only `jev` and `decompose` continue; a
   `code` verdict answers the request with plain code and no caller, an `llm` verdict keeps the model
   that already writes the text, and `hybrid` is split first. State the verdict in one line.
2. **Route and language decision.** Pick the route from the order in [`./providers.md`](./providers.md)
   and the language from the repository. Say which route and which language were chosen, because the
   question type name and the confidence path change with the route.
3. **Constants file first.** Write the file holding `QUESTIONS` and `THRESHOLDS` before the caller.
   Thresholds carry a comment marking them as untuned assumptions until the user's own data says
   otherwise. The caller imports from this file so a person reviews one place.
4. **Call file.** Write the single caller for the chosen route and language: read the key from the
   environment by name at call time, send one state with all questions in one request, and never print,
   log, or write the key.
5. **Request check with the offline checker.** Assemble the same questions into a request file and run
   `bash scripts/check-jev-request.sh --route <route> <file>`, run from the skill folder, where `--route` is one of `direct`,
   `bai`, or `aisdk`. Exit 0 is required before the caller is handed over; exit 1 names the field to
   fix. When bash or jq is unavailable, run the checklist in [`./question-design.md`](./question-design.md) by
   hand and say so.
6. **Response validation.** The caller checks every answer before acting on it: every question id sent
   is present in the response, the answer type matches the question type sent, a `choice` answer is one
   of the criteria keys, a `score` answer falls inside the level range, a probability falls between 0
   and 1, and a distribution sums to 1 inside a small tolerance. A response that fails any of these is
   an error, not a value to coerce.
7. **Confidence-gated branch.** Route by certainty instead of trusting one number. A `noul` answer is
   branched on its probability; `choice` and `score` answers are branched on `confidence`. The low band
   returns a `review` path that sends the item to a person, and the band boundary is a named constant
   from step 3 rather than a literal in the caller.
8. **Consent before any live call.** The generated code does not call the service on its own. Before the
   first live request, ask the person, say what the call will cost using
   [`./official/jev-platform.md`](./official/jev-platform.md), and keep the run to the smallest number
   of requests that answers the question. Confidence, a key in the environment, or the checker passing
   is not consent.
9. **Stop.** Hand over the three files, the checker result, and the route and language decisions. Do not
   run a live call inside this mode.

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

1. Write `request.json` with a sample state, one yes/no question (named `noul` on the direct and b.ai
   routes and `boolean` on the AI SDK route), one `choice`, and one `score` question, and a
   model field that carries the id the snapshot lists as accepted for the chosen route; the constants
   header records the snapshot date and says to re-check it before the first call, because a placeholder
   cannot pass the checker on a b.ai route.
2. Write the constants file with `QUESTIONS` and `THRESHOLDS` exported together, thresholds marked as
   untuned assumptions.
3. Write the routing table mapping each answer to the code path that acts on it, including the low
   confidence row.
4. Run the checker on `request.json` for each route the template is meant to serve. The template in this
   package passes both `direct` and `bai`; a template written for the SDK route is checked with
   `--route aisdk`.
5. Put the replace-before-call note in the constants file header and in the report; a JSON file gets
   none, because a note key would come back as an unknown field from the checker.

**Output files and location.** `request.json`, `constants.ts`, and `routing-table.json` under the
default location or the path the user gave.

**Verification.** The checker exits 0 for every route the template claims, and the routing table has a
row for every answer the questions can produce.

**Stop when** the three files exist, every claimed route passes the check, and the replace-before-call
note is present in the constants header and the report.

## eval

**Signals.** "Evaluate", "test set", "labels", "thresholds", "how accurate", "before we ship". Korean:
"평가", "라벨", "임계값", "정확도", "검증 세트".

**Required inputs and defaults.** The decision being made, the questions, and as many labeled examples
as the user has. With no labels, the plan says where they come from and treats the first batch as
provisional.

**Steps.**

1. Write the decision down and price each error type: a false positive and a false negative rarely cost
   the same, and the threshold follows the cost rather than the accuracy.
2. Build the case set: representative cases, then the hard ones. The hard list starts with negation,
   quoted third-party text, two intents in one message, missing information whose expected label is
   null, an instruction embedded inside the state, and informal Korean.
3. Split the cases into a tuning set and a frozen test set, and freeze the test set before tuning
   anything.
4. Pin the model version for any comparison whose result must hold still. See
   [`./eval-and-audit.md`](./eval-and-audit.md) for the pinned version id and why an alias is the wrong
   choice there.
5. Calibrate thresholds on the tuning set, then report on the frozen set. Draw the review band from the
   cost of each error, not from the accuracy curve alone.
6. Name the baselines the result is compared against, including the current rule or regex where one
   exists.
7. Before any live measurement, the safety rules apply: the person's consent for the call, separate
   consent when the state carries private data, and one request first, in the smallest useful shape.
   State the estimated cost from [`./official/jev-platform.md`](./official/jev-platform.md).

**Output files and location.** `eval-plan.md` and `eval-cases.jsonl` under the default location or the
path the user gave. Case rows carry the expected label, including a null label where the honest answer
is "not enough information".

**Verification.** The plan names the tuning set, the frozen set, and the measurement that decides each
threshold, and the case rows carry their expected labels including the null rows.

**Stop when** the plan defines both error costs, the two sets are separate, and the tuning procedure is
written. This mode produces the plan, the case template, and the tuning procedure; it does not run the
live measurement itself.

## audit

**Signals.** "Audit", "find the LLM calls", "what should we replace", "where do we waste calls". Korean:
"감사", "LLM 호출 찾아", "교체 대상", "어디서 낭비하나".

**Required inputs and defaults.** A repository path and, if the user has one, the list of files they
care about. Default scope is the whole working tree minus dependencies and generated code.

**Steps.**

1. Find every place an LLM is called and only a label comes back: the answer set is finite, the caller
   parses the reply into one of those values, no person reads the reasoning, and the call runs often or
   a person waits on it.
2. Disqualify the calls a judgment model cannot serve, using the documented limits: anything needing
   arithmetic, counting, date comparison, multi-hop reasoning, or generated text stays where it is.
3. Measure each remaining call: calls per day, p50 and p95 latency, tokens per call, and what is blocked
   while it runs.
4. Rank by what the swap would save and by how small the change is.
5. Write the table, then stop.

**Output files and location.** A single report, `audit.md`, written under `.hyper/jev-maker/<topic>/`
outside the tree being audited, or given in the reply, or at the path the user gave when that path is
outside the audited tree. Nothing else is written.

**Verification.** Every row cites a file and line, the report was produced without editing any file in
the audited tree, and the report itself sits outside that tree.

**Stop when** the table is written and the working tree is unchanged. This mode is read-only: it finds
candidates and never rewrites them.

## provider

**Signals.** "Which provider", "which route", "connect it", "setup", "environment". Korean: "어느 경로",
"어디로 연결", "설정", "환경 변수".

**Required inputs and defaults.** The repository, and the name of the key the user already has, checked
by name only.

**Steps.**

1. Decide the route with the order in [`./providers.md`](./providers.md), starting from what the
   repository already depends on.
2. Check which environment variable names exist, never their values, and report the answer as a name.
3. Write the setup steps for the chosen route alone, including where the key is read and what must not
   be logged. The setup document names the environment variable and the route, and points at
   [`./providers.md`](./providers.md) and [`./official/jev-platform.md`](./official/jev-platform.md) for
   the accepted model ids and the endpoint; it does not copy them into prose, because they are refreshed
   in those files.
4. If the user named a route that carries no verified contract, say so and produce no code for it.
5. State the first-call rule: one live request, after consent, with the cost named first.

**Output files and location.** `provider-setup.md` under the default location or the path the user
gave.

**Verification.** The chosen route has a verified row in [`./providers.md`](./providers.md), the
environment variable is named rather than valued, and no key value appears in the document.

**Stop when** the setup document names the route, the environment variable, and the first-call rule, and
no live call was made.

## Sources

> Links checked 2026-10-01.

| Claim | Source |
| --- | --- |
| The mode set, the per-mode signals, and the fit gate that runs first | [`../rules/modes-and-routing.md`](../rules/modes-and-routing.md) |
| The shape of a question, the `what`/`not_for`/`examples` criteria, and the manual checklist used when bash or jq is missing | [`./question-design.md`](./question-design.md) |
| The route order, the key handling rule, and the routes that carry no verified contract | [`./providers.md`](./providers.md) |
| The output path default and the no-overwrite rule | repository policy |
| The question types and the answer fields validated after a call | <https://docs.typesafe.ai/api> |
| The limits that disqualify a call from a judgment model, used by `design` and `audit` | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| The confidence ranges and the review path behind the confidence-gated branch | <https://docs.typesafe.ai/confidence> |
| The single-constants-file habit and the warning that a stale copy makes an agent invent fields | <https://docs.typesafe.ai/agent-skill.md> |
| The offline checker's flags, exit codes, and route names | `../scripts/check-jev-request.sh` |

### Evidence grade

`LOCAL` for the shared rules, the per-mode steps, and the stop conditions: they are this package's
procedure built on the repository's own routing and question guidance. `VENDOR` for the question
shapes, the answer fields, the documented limits, and the confidence guidance, each carried by the
linked page. `PRIMARY` for the checker row, which was read from the file in this package rather than
from a description of it.

Prices, rate limits, context budgets, endpoint names, and model aliases are deliberately absent here.
They live in [`./official/jev-platform.md`](./official/jev-platform.md) and
[`./providers.md`](./providers.md), behind a review date.
