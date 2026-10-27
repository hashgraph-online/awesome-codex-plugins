# Stress-testing settled answers and held plans

Supporting detail for [Interview](../SKILL.md): both tests ask in its question
shape, and what they settle lands in its lists.

## Test the settled answers

Run this once before handoff, after a stop condition holds and while the
caller is still in the conversation. If the caller has stopped, skip it.

1. **Read the answers together**, including recommendations accepted with
   "your call". Each was settled on its own; look for answers that cannot all
   hold and effects the caller has not traced. Typical cases: proof that needs
   an action the authority forbids, such as a Git push; a budget too small for
   the acceptance; a non-goal that removes something a criterion needs. Ask
   one question per finding.
2. **Try borderline cases.** Put up to three proposals that could go either
   way, recommending what the settled answers imply. Aim at fault lines: an
   addition just outside the outcome, work that would starve another
   criterion, or a result that passes the proof while the outcome still fails.
   Take them from open issues or recent work rather than inventing them, and
   skip any whose answer is obvious.
3. **Route each answer.** When the settled answers already decide the case,
   move on. When they cannot, sharpen the outcome or acceptance instead of
   adding a criterion to absorb the case. When the caller rejects the
   proposal, record it as a non-goal.

## A plan the caller already holds

When the caller selects Interview to test a plan, design or decision they
already have, its choices become the branches.

- Each choice the plan states or quietly depends on is a branch. Recommend
  keeping or changing it, with reason and tradeoff; the caller decides. Check
  a choice a source settles yourself instead of asking.
- Order branches as usual: the outcome first, then the ones that most change
  acceptance, scope or authority, prerequisites before dependents.
- The one-slice stop does not apply. Stop when the caller stops or every
  branch the plan relies on is decided or listed as Open.
- Hand the lists back. The caller revises the plan or takes it to
  [Plan](../../plan/SKILL.md); Interview does not rewrite it.
