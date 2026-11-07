# Modes and Routing

**Purpose**: Pick the right mode from the shape of the request, decide whether the request belongs to Jev at all, and fill the gaps a request usually leaves open.

Every request settles three things, in this order: which mode, whether Jev is the right tool, and which defaults apply where the request is silent. Read the mode from the artifact the user wants, not from the keyword they used. A request that says "classify" but asks for a Python file wants the code mode.

## 1. Mode Detection

Look at the artifact the user expects to open, and match it to one row. When two rows look close, take the one whose artifact the user reads first.

| Mode | English signals | Korean signals | Produced artifact |
|---|---|---|---|
| `design` | "should this use Jev", "is this a judgment problem", "Jev or code", "decision contract", "how should I split this" | "Jev로 하는 게 맞나", "판단 문제인가", "결정 계약", "어떻게 나눌까" | Fit verdict plus a decision contract: what each part decides, who owns it, and where review sits |
| `questions` | "write the questions", "question set", "criteria", "options", "scale" | "질문 만들어", "질문 묶음", "선택지", "기준", "점수 단계" | A question set ready to paste into a request |
| `code` | "call it from", "integration code", "client", "wire this into", "TypeScript", "Python" | "호출 코드", "연결 코드", "클라이언트", "연동" | Call code for one route and one language |
| `template` | "request json", "constants file", "routing table", "starter", "skeleton" | "요청 JSON", "상수 파일", "라우팅 표", "템플릿", "뼈대" | Request JSON, a constants file, and a routing table |
| `eval` | "evaluate", "test set", "labels", "thresholds", "how accurate", "before we ship" | "평가", "라벨", "임계값", "정확도", "검증 세트" | Evaluation plan, case skeleton, and a threshold-tuning plan |
| `audit` | "audit", "find the LLM calls", "what should we replace", "where do we waste calls" | "감사", "LLM 호출 찾아", "교체 대상", "어디서 낭비하나" | Ranked audit table over existing calls, read-only |
| `provider` | "which provider", "which route", "connect it", "setup", "environment" | "어느 경로", "어디로 연결", "설정", "환경 변수" | Route choice and a setup guide |

One request can land on two rows, as in "design it and give me the code". Run the rows in the order the user reads the artifacts, and say which mode you ran.

## 2. Fit Gate

Run this gate before any mode runs. It is five questions, answered in order.

1. Can the answer be one of a closed set of options, a point on an ordered scale, or a yes/no verdict?
2. Could exact code produce the same answer with no model involved?
3. Does the output have to be newly written prose or newly written code?
4. Does the answer depend on arithmetic, counting, or multi-step reasoning over numbers?
5. Is the input text, rather than an image, audio, or a database row that code can read directly?

Then read the verdict.

Read the rows top to bottom and take the first that applies. Q1 = no means the answer is not a closed
set, a scale, or a yes/no, so treat it as `llm` (Q3 yes) or `code` (Q2 yes) by the question that
decides it; when neither applies, say the request is not a Jev judgment and offer a plain alternative.

| Verdict | When it applies | What to do |
|---|---|---|
| `jev` | Q1 yes, Q2 no, Q3 no, Q4 no, Q5 yes | Run the mode. Build the question set or the call, state the fallback option, and give the low-confidence band a review path. |
| `decompose` | Q4 yes, and the request also contains a judgment part that passes Q1, Q2 = no, Q3 = no, Q5 yes | Return a design that splits the work. Code owns the arithmetic and the policy, Jev owns the judgment, and each half is re-checked against this gate. |
| `code` | Q2 yes, or Q4 yes, or Q5 no | Stop. Say why code answers it exactly, runs offline, and is testable, and produce no Jev artifact. Offer the plain code path instead. |
| `llm` | Q3 yes | Stop. The deliverable is generated text or generated code, and a judgment model picks among options instead of writing. Keep the model that already does this. |
| `hybrid` | The request mixes a judgment part with a generation part; checked before `llm` when the request mixes judgment and generation | Produce no Jev artifact yet. Split it first: name which sentence goes to Jev and which goes to a language model, then run only the Jev half. |

Worked rows:

| Request | Verdict | Why |
|---|---|---|
| "compute the difference between two dates" | `code` | Date arithmetic has one exact answer. A date library gets it right, and a judgment model is documented as unreliable on dates. |
| "write a reply email" | `llm` | The deliverable is new prose. A judgment model selects among given options and does not write. |
| "classify these tickets into 5 queues" | `jev` | Five queues are a closed set, each ticket is text, and the task is one selection per ticket. |
| "score these leads 1 to 10 on fit" | `jev` | An ordered scale with bounded steps, over text input. |
| "decide whether this clause is risky and rewrite it if it is" | `hybrid` | The risk call is a yes/no over text; the rewrite is generation. |
| "work out the refund amount and decide whether it needs approval" | `decompose` | Code computes the amount from the rules; Jev judges the approval question. |
| "summarize this document" | `llm` | Summarizing produces text that does not exist yet. |

When the verdict is not `jev`, say so plainly and give the alternative. Do not soften the answer into a Jev artifact that will be wrong.

The gate runs on the decision the request wants Jev to make. In `audit` it runs once per candidate call, before that call is listed. `provider`, and any request whose deliverable is an action rather than a judgment, such as "put this key in code and run it", produce no Jev artifact, so the gate does not apply there and the safety rules decide whether the run continues or stops. A run can also end at those safety rules, or at a missing permission, before any verdict is reached.

## 3. Required-Input Defaults

Fill these from the repository before asking anything.

- **Language.** `package.json` present and `pyproject.toml` absent means TypeScript. `pyproject.toml` present means Python. Neither present, or both present, means TypeScript. Say which one you picked in a single line.
- **Route.** Take the order from the provider reference at [`../references/providers.md`](../references/providers.md) and follow it from the top down. Do not invent a route the reference does not list.
- **Model and contract details.** Read them from [`../references/official/jev-platform.md`](../references/official/jev-platform.md). Do not restate them inside a generated artifact as if they were fixed.
- **Ambiguity.** Proceed with the closest mode and ask exactly one missing fact. Pick the fact whose answer changes the artifact, not the fact that is easiest to ask. Never open a task with a batch of questions.

## 4. Output Location

Write artifacts where the user asked, when they asked. Otherwise write under `.hyper/jev-maker/<topic>/`, with `<topic>` a short slug taken from the request.

```text
.hyper/jev-maker/<topic>/
├── request.json
├── constants.ts
└── eval-cases.jsonl
```

An existing file is never overwritten without confirmation. Read it first, then write a sibling file or ask before replacing it. Report the path of every file you wrote.

## Sources

> Links checked 2026-10-01.

| Claim | Source |
|---|---|
| The mode set, the mode signals, the one-missing-fact rule, and the fit-gate questions | user instruction, 2026-10-01 |
| Jev's documented limits on dates, counting, arithmetic, and text generation, which drive the `code`, `llm`, and `decompose` verdicts | `../references/official/jev-platform.md` |
| The language defaults, the route order, and what each route reads | `../references/providers.md` |
| The output path default and the no-overwrite rule | repository policy |

### Evidence grade

`LOCAL`: the routing rules are repository policy and a user instruction. `VENDOR`: Jev's documented limits, which are carried by the linked snapshot rather than restated here.
