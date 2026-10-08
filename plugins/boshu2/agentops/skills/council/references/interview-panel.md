# Interview panel: the council answers an Interview

Loaded by [Council](../SKILL.md) when the caller asks a council to answer an
[Interview](../../interview/SKILL.md).

Interview is human-invoked. When the caller asks a council to answer it,
Interview still asks one question at a time and Council stands in as answerer.

1. Send each question to every member in a fresh sealed context with the same
   evidence; only the synthesized answers to earlier questions travel, labeled
   provisional, never a peer's raw answer. Each member returns an answer in
   Interview's shape: recommendation, reason, and tradeoff.
2. Mark answers the members agree on as **council-agreed**. Keep divergent
   answers open, each position with its evidence.
3. After the question set, or at Interview's stop condition, run one bounded
   debate on the open disagreements under the [debate](debate.md) rules. Vote
   on an exact candidate only if the caller chose a majority rule.
4. Return the synthesized answers with dissent. The caller accepts or amends
   them in one pass before Interview records anything.

The council may recommend authority, budgets, Git or external write
permission, and acceptance changes to a running goal. It never grants or makes
them; those answers stay the caller's even in this mode.

It's working if nothing reaches Interview before the caller accepts it.
