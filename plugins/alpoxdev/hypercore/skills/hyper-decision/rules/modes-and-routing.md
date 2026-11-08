# Modes and Routing

**Purpose**: Pick the right mode from the shape of the request, decide whether the request belongs to a decision model at all, place it on a route tier, and fill the gaps a request usually leaves open.

Every request settles four things, in this order: which mode, whether a decision model is the right tool, which route tier serves it, and which defaults apply where the request is silent. Read the mode from the artifact the user wants, not from the keyword they used. A request that says "classify" but asks for a Python file wants the code mode.

## 1. Mode Detection

Look at the artifact the user expects to open, and match it to one row. When two rows look close, take the one whose artifact the user reads first.

| Mode | English signals | Korean signals | Produced artifact |
|---|---|---|---|
| `design` | "should this use a decision model", "is this a judgment problem", "model or code", "decision contract", "how should I split this" | "결정 모델로 하는 게 맞나", "판단 문제인가", "결정 계약", "어떻게 나눌까" | Fit verdict plus a decision contract: what each part decides, who owns it, and where review sits |
| `questions` | "write the questions", "question set", "criteria", "options", "levels", "scale" | "질문 만들어", "질문 묶음", "선택지", "기준", "점수 단계" | A question set ready to paste into a request, in the route's dialect |
| `code` | "call it from", "integration code", "client", "wire this into", "TypeScript", "Python" | "호출 코드", "연결 코드", "클라이언트", "연동" | Call code for one route and one language |
| `template` | "request json", "constants file", "routing table", "starter", "skeleton" | "요청 JSON", "상수 파일", "라우팅 표", "템플릿", "뼈대" | Request JSON, a constants file, and a routing table |
| `eval` | "evaluate", "test set", "labels", "thresholds", "how accurate", "compare models", "before we ship" | "평가", "라벨", "임계값", "정확도", "모델 비교", "검증 세트" | Evaluation plan, case skeleton, and a threshold-tuning plan |
| `audit` | "audit", "find the LLM calls", "what should we replace", "where do we waste calls" | "감사", "LLM 호출 찾아", "교체 대상", "어디서 낭비하나" | Ranked audit table over existing calls, read-only |
| `provider` | "which provider", "which route", "Jev or GPT", "gateway", "connect it", "setup", "environment" | "어느 공급자", "어느 경로", "어디로 연결", "설정", "환경 변수" | Route and tier choice and a setup guide |

One request can land on two rows, as in "design it and give me the code". Run the rows in the order the user reads the artifacts, and say which mode you ran.

## 2. Fit Gate

Run this gate before any mode runs. It is five questions, answered in order.

1. Can the answer be one of a closed set of options, a point on an ordered scale, a yes/no verdict, or a region in an image?
2. Could exact code produce the same answer with no model involved?
3. Does the output have to be newly written prose or newly written code?
4. Does the answer depend on arithmetic, counting, date comparison, or multi-step reasoning over numbers?
5. Is the input text, JSON, or an image a route accepts, rather than audio, video, or a database row that code can read directly?

Then read the verdict.

Read the rows top to bottom and take the first that applies. Q1 = no means the answer is not a closed set, a scale, a yes/no, or a region, so treat it as `llm` (Q3 yes) or `code` (Q2 yes) by the question that decides it; when neither applies, say the request is not a decision-model judgment and offer a plain alternative.

| Verdict | When it applies | What to do |
|---|---|---|
| `decision` | Q1 yes, Q2 no, Q3 no, Q4 no, Q5 yes | Run the mode. Build the question set or the call, give every choice a way to say no option fits, and give the low-confidence band a review path. |
| `decompose` | Q4 yes, and the request also contains a judgment part that passes Q1, Q2 = no, Q3 = no, Q5 yes | Return a design that splits the work. Code owns the arithmetic and the policy, the decision model owns the judgment, and each half is re-checked against this gate. |
| `code` | Q2 yes, or Q4 yes with no judgment part, or Q5 no | Stop. Say why code answers it exactly, runs offline, and is testable, and produce no decision artifact. Offer the plain code path instead. |
| `llm` | Q3 yes | Stop. The deliverable is generated text or generated code, and a decision model picks among options instead of writing. Keep the model that already does this. |
| `hybrid` | The request mixes a judgment part with a generation part; checked before `llm` when the request mixes judgment and generation | Produce no decision artifact yet. Split it first: name which sentence goes to the decision model and which goes to a language model, then run only the decision half. |

Two checks sharpen a `decision` verdict before generation:

- **Judgments, not the decision.** A question that asks the model to make the business decision ("should this ticket be escalated?") is usually at the wrong layer. Ask for the judgments the decision rests on (is the customer angry, is money at stake, is this a security report), and keep the decision as a truth table in code.
- **Human test.** A capable person handed only this state and this question should be able to answer at once. If they would need another document, a lookup, or a calculation, move that work into code or into the state first.

Worked rows:

| Request | Verdict | Why |
|---|---|---|
| "compute the difference between two dates" | `code` | Date arithmetic has one exact answer, and decision models are documented as unreliable on dates. |
| "write a reply email" | `llm` | The deliverable is new prose. A decision model selects among given options and does not write. |
| "classify these tickets into 5 queues" | `decision` | Five queues are a closed set, each ticket is text, and the task is one selection per ticket. |
| "score these leads 1 to 10 on fit" | `decision` | An ordered scale with bounded steps, over text input. |
| "find where the damage is in this product photo" | `decision` | A region in an image; only routes that list the box type serve it. |
| "decide whether this clause is risky and rewrite it if it is" | `hybrid` | The risk call is a yes/no over text; the rewrite is generation. |
| "work out the refund amount and decide whether it needs approval" | `decompose` | Code computes the amount from the rules; the decision model judges the approval question. |
| "summarize this document" | `llm` | Summarizing produces text that does not exist yet. |

When the verdict is not `decision`, say so plainly and give the alternative. Do not soften the answer into a decision artifact that will be wrong.

The gate runs on the decision the request wants the model to make. In `audit` it runs once per candidate call, before that call is listed. `provider`, and any request whose deliverable is an action rather than a judgment, such as "put this key in code and run it", produce no decision artifact, so the gate does not apply there and the safety rules decide whether the run continues or stops. A run can also end at those safety rules, or at a missing permission, before any verdict is reached.

## 3. Route Tiers

Every route belongs to one tier, and the tier decides what the generated artifact may assume. The route rows, endpoints, and dialects live in [`../references/providers.md`](../references/providers.md); this table only says what each tier promises.

| Tier | What it is | Returns probabilities | What the artifact does |
|---|---|---|---|
| T1 | A native decision API that answers typed questions over a state | Yes, per the vendor reference, with vendor-specific gaps (a boolean may carry no confidence; a box always returns edges) | Thresholds on the selected option's probability, a review band, a pinned versioned model id where offered |
| T2 | An SDK or gateway in front of T1 or T3 routes | Only when the routed model is native; the SDK or gateway does not add calibration | Same as the routed tier, plus the SDK or gateway version pinned and a note on what the abstraction hides |
| T3 | Emulation on a general LLM: structured output with an enum, plus token log probabilities only where the vendor still returns them | Usually no distribution; a prompted self-estimate is not a calibrated probability | A review path instead of a threshold, unless a documented probability source exists and is validated on labeled data |
| T4 | A fixed-taxonomy classifier, guardrail, or judge | Scores or ordinal grades over the vendor's own labels, not the caller's | Named in an audit or a design as a policy filter, never generated as a decision route |

When the user needs a probability to act on, never pick a T3 route silently: say that it returns none and offer a T1 route or a review path, and let the user choose.

## 4. Required-Input Defaults

Fill these from the repository before asking anything.

- **Language.** `package.json` present and `pyproject.toml` absent means TypeScript. `pyproject.toml` present means Python. Neither present, or both present, means TypeScript. Say which one you picked in a single line.
- **Route.** Take the order from the route choice section of [`../references/providers.md`](../references/providers.md) and follow it from the top down. Project files outrank environment variable names. Do not invent a route the reference does not list.
- **Model and contract details.** Read them from the matching file under [`../references/official/`](../references/official/). Do not restate them inside a generated artifact as if they were fixed.
- **Ambiguity.** Proceed with the closest mode and ask exactly one missing fact. Pick the fact whose answer changes the artifact, not the fact that is easiest to ask. Never open a task with a batch of questions.

## 5. Output Location

Write artifacts where the user asked, when they asked. Otherwise write under `.hyper/decision/<topic>/`, with `<topic>` a short slug taken from the request.

```text
.hyper/decision/<topic>/
├── request.json
├── constants.ts
└── eval-cases.jsonl
```

An existing file is never overwritten without confirmation. Read it first, then write a sibling file or ask before replacing it. Report the path of every file you wrote.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
|---|---|
| The mode set, the mode signals, the one-missing-fact rule, and the fit-gate questions | user instruction, 2026-10-01; widened to decision APIs in general by user instruction, 2026-11-08 |
| Asking for judgments rather than the decision, the truth table in code, and the human test for state design | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| Decision models' documented limits on dates, counting, arithmetic, and text generation, which drive the `code`, `llm`, and `decompose` verdicts | `../references/official/jev-platform.md` |
| The four tiers and which routes return probability distributions | `../references/providers.md`, `../references/official/decision-providers.md` |
| The language defaults, the route order, and what each route reads | `../references/providers.md` |
| The output path default and the no-overwrite rule | repository policy |

### Evidence grade

`LOCAL`: the routing rules and the tier split are repository policy and user instruction. `VENDOR`: the judgments-not-decisions rule and the human test come from the vendor's published skill, and the decision models' documented limits are carried by the linked snapshots rather than restated here.
