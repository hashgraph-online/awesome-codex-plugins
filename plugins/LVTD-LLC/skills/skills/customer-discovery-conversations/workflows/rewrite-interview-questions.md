# Rewrite Interview Questions

Use this workflow when a user provides planned customer interview questions.

## Steps

- [ ] Identify the business decision or risk each question should inform.
- [ ] Mark questions that ask for opinions, approval, hypotheticals, generic
  behavior, or feature ideas.
- [ ] Rewrite toward recent examples, current workflows, past attempts, costs,
  constraints, existing budgets, and people involved.
- [ ] Add follow-ups that dig into strong emotion, workarounds, switching costs,
  and why the current approach persists.
- [ ] Remove questions that would still be nice-to-have trivia even if answered.
- [ ] Keep the guide short enough to use in a natural conversation.

## Output

Return a table with: `Original`, `Issue`, `Rewrite`, and `Follow-up`. If a
question should be removed, say what decision it fails to inform.

## Rewrite Patterns

| Weak Question Type | Better Direction |
|--------------------|------------------|
| Do you like this idea? | Ask how they handle the underlying problem today. |
| Would you buy this? | Ask what they already pay, lose, or do to solve it. |
| What features do you want? | Ask what the request would let them accomplish. |
| What do you usually do? | Ask about the most recent specific instance. |
| What is your biggest problem with X? | First confirm whether X matters at all. |

## Exit Criteria

The revised guide has three or fewer core learning goals, avoids pitching, and
can produce evidence that changes a product, segment, positioning, or sales
decision.
