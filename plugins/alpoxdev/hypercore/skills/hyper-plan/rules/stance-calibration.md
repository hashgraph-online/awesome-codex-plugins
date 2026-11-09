# Stance Calibration

Use this file in the question phase of `planning-workflow.md`, before and after every question. It owns the question form, the classification of a reply, and the scope a delegation phrase settles. The two filters, the per-turn cap of three questions, and the owner-decision list stay in that workflow.

## 1. Question Forms

| Form | Shape | Switch to it when | Leave it when |
|---|---|---|---|
| Batch (default) | one to three questions in one turn, each with the recommendation first, answered in any order | a turn starts | a switch condition below holds |
| One by one | one question per turn, sent only after the previous answer is read | an answer changes which later questions survive or what their options are | no surviving question depends on the last answer |
| Examples first | two or three worked examples, each an input and the plan behaviour it produces, shown before the option labels | the user cannot judge an abstract option, or asks for an example ("예시로 보여줘") | the user answers from the examples and states a preference |

- Batch is the default. A turn switches form only on the stated condition and says in one phrase which form it is using.
- The cap belongs to the turn, not to the interview: one by one spends the same cap across turns, and no form asks more than three questions in one turn.
- An examples-first turn still ends with two to four options and the recommendation first. It never asks the user to design the options or to supply the examples.
- A form applies to the fork in hand. Return to batch when the switch condition ends, and let a declared preference in §4 outrank both switches.

## 2. Reply States

Classify every reply into exactly one state before the next turn. The state decides whether the fork is closed, narrowed, or abandoned.

| State | Signal | Recorded as | Next turn |
|---|---|---|---|
| `resolved` | names an option or a decision, with enough information to act on it | the decision, in `## Decisions` | continue; never re-ask it |
| `resolved_uninformed` | takes the recommendation or passes on the fork without the facts behind it ("추천대로", "그걸로", "다 괜찮아", a skipped question) | the decision in `## Decisions`, plus an open-assumptions row marked `uninformed` | continue; the plan marks the decision as uninformed |
| `unresolved_progress` | answers part of it, adds a constraint, or narrows the fork with a counter-question | the new information, then the narrowed question | ask the remaining part; it counts against that turn's cap |
| `unresolved_blocked` | cannot be answered now: the answer waits on a fact the user does not have, a decision by someone else, or an outside event | the blocker, who or what can clear it, and the default adopted meanwhile | stop asking it; adopt the recommendation and carry the blocker as a plan risk |

- A `resolved_uninformed` reply is never upgraded to `resolved` by the planner's own reading. The recommendation nobody checked is recorded as the decision and marked `uninformed` in the draft's open-assumptions row and in the plan's `Decisions made for you:` line, so the executor can see that no fact stands behind it.
- A bare acknowledgement ("ㅇㅇ", "ok") answers an open question as `resolved_uninformed` on the recommended option. With no open question it settles nothing and stays out of `## Decisions`.
- `unresolved_blocked` still delivers a plan: adopt the recommendation, record the assumption with its reversibility, and put the blocker in the plan's risk line. It never becomes the same question again on the next turn.
- Asking again about a `resolved` or `resolved_uninformed` fork is a defect. The draft already holds the decision, and the repeat spends the cap while reading as not having listened.

## 3. Delegation Scope

A delegation phrase is a speech act, not a blank cheque. Read its words and apply the narrowest scope that fits them.

| Scope | Phrases | What it settles |
|---|---|---|
| Question | "이건 그걸로", "이 질문은 네가 정해", "whatever you think for this one" | the current question only |
| Topic | "이 부분은 알아서 해", "로그인 쪽은 니가 정해", "이 주제는 알아서" | every open question on the topic that turn is about, and nothing outside it |
| Plan | "전부 알아서", "다 알아서 해", "질문 그만, 전부 알아서", "stop asking, decide everything" | every remaining fork in the plan, including later topics |

- An unqualified "알아서 해", "니가 정해", or "질문 그만" is topic-scoped. It never widens to the plan by itself; only a plan word in the same reply ("전부", "다", "everything", "계획 전체") does that.
- "질문 그만" without a scope word ends the questions for the current topic. It is never read as consent for the rest of the plan.
- A delegated fork is recorded in `## Decisions` with the quoted phrase and the scope it settled, for example `delegation: "이 부분은 알아서 해" -> topic: login rate limit`, so a later turn neither re-asks it nor widens it.
- After a plan-scoped delegation the planner raises only two kinds of message: a fork whose answer risks irreversible loss (a destructive change, an unrollbackable migration, a new spend, an external send or publication, lost data), or a step only the user can perform (a credential, an account or permission approval, a login, a payment). Each message names which of the two it is.
- Everything else is decided by the planner and written into the open-assumptions ledger with its reversibility. Naming, structure, library, file layout, response codes, defaults, and test strategy are planner calls at that point.
- A delegation settles planning forks only. It never lowers the review requirement, skips the structural self-check, or authorizes implementation, and the skill still writes only the draft and the plan.

## 4. Question-Form Preference

How the user prefers to be asked is recorded in the draft and holds for the rest of the run.

- Two draft frontmatter fields carry it: `question_form: batch | one_by_one | examples_first` and `question_form_source: declared | observed`.
- `declared` is set the moment the user says how they want to be asked ("한 번에 다 물어봐", "하나씩 물어봐", "예시로 보여줘", "ask them all at once"). It outranks every switch in §1 and every `observed` value.
- `observed` is set only after two replies point the same way: two answers that pass on a whole batch support `batch`; a reply that answers one question and drops the others supports `one_by_one`; a request for a worked example supports `examples_first`. One reply is a data point, not a preference.
- A later reply that contradicts the record replaces it and notes the change in `## Questions asked` with its new provenance.
- The record lives in the draft, so it survives compaction and a resumed session, and it is never stored in runtime memory, a settings file, or anywhere outside the run. This file does not carry a preference across sessions.

## 5. Worked Example

A batch turn asks three questions about login rate limiting: the limit, the counter store, and the response code.

```text
User: 이 부분은 알아서 해. 대신 감사 로그는 따로 남겨줘.
```

- The phrase is topic-scoped, so the three login questions become `resolved_uninformed` on their recommendations and are marked `uninformed`. The audit-log sentence is `unresolved_progress`: it adds a constraint rather than reopening a fork.
- The next topic, a notification refactor, is still asked, because the delegation ended at the login topic.
- A later "질문 그만, 전부 알아서" is plan-scoped. The remaining forks are decided and recorded, and the planner returns only for an irreversible loss (deleting a production table) or a user step (the deploy credential).

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Question forms of batch, one by one, and examples first; the four reply states; delegation phrases read as speech acts with the narrowest fitting scope; question-form preference recorded with declared or observed provenance | `dbc-hbin/omp-ulw` at commit `74df40f` (2026-11-09); the source repository has no license, so the mechanism was re-authored, not copied |
| The two filters, the three-question cap, the owner-decision list, and the recommendation-first shape that this file extends | `rules/planning-workflow.md` §6 |
| The draft frontmatter fields and the open-assumptions ledger that hold the record | `rules/planning-workflow.md` §7 |
| The two conditions that survive a plan-scoped delegation: irreversible loss and a step only the user can perform | the owner-decision list in `rules/planning-workflow.md` §6, narrowed here to those two |
| A preference kept in durable state rather than in memory or a settings file | `instructions/context-engineering/references/context-management.md` |

### Evidence grade

`LOCAL` - this file states this package's own question procedure. The three forms, the four states, and the three delegation scopes are this package's chosen vocabulary, re-authored from the idea in the upstream planner; the counts are this package's bounds, not validated optima.