# Grilling Mode Reference

`SKILL.md` owns entry signals, mode precedence and the no-implementation gate.
This reference owns the selected interview procedure: opening, pace, questions
and exit. Do not load this file unless Grilling Mode is already active.
Normal design and soft-intent confirmation do not load this procedure.

## Opening Card

Emit this once, in the user's language, then begin the interview:

```text
◆ Grilling Session
Target: <idea / plan / design>
Question path: value -> boundaries -> failure modes -> acceptance
Pace: deep (default) | fast (user-requested)
```

## Interview Procedure

### Pace

- **Deep:** Ask exactly one decision question per turn when it is blocking or depends on the previous answer. State the recommended answer and the most relevant trade-off before waiting.
- **Fast:** Only when the user explicitly asks for a fast or batched interview (for example, `fast`, `batch`, `快问`, or `一次问几个`), ask at most three independent decision questions. Give each question its recommendation and trade-off, then wait for the user's responses. Return to deep pace for dependent follow-ups.

1. Explore the codebase and current authority docs for facts before asking. Do not ask the user for facts that can be found locally.
2. The user owns the decision. Do not treat a recommendation, a tentative answer, or a shared-understanding checkpoint as final approval.
3. Aside from the one-time opening card, keep the turn to the observation, recommendation, and the selected pace's questions. Do not emit a full design ceremony, write docs, create a plan, or implement while the interview is active.
4. End when the user says to stop, defer, or that the questions are sufficient. Reconfirm in a structured `Challenge Result`. That summary does not grant completion authority.

```text
Challenge Result
- Survived assumptions
- Rejected assumptions
- New evidence needed
- Design changes required
- Residual risks
- Return state: interview | design | approaches | writing-plans
```
5. If the user asks to proceed after the interview, return to the normal brainstorming design gate. A design/spec still needs the required approval before planning or implementation.
