# Custom Advisor Template

Copy this structure to add a seat. Save custom advisors to `.agents/advisors/<kebab-name>.md` in the user's project (not inside the skill folder) so they survive skill updates.

Two kinds of custom seats:

- **A role** the bench lacks (for example "Channel Partner Lead" or "Regulated-Industry Marketer"). Write it the way the built-in dossiers are written: a lens, Suede-named frameworks in your own words, default positions, and blind spots. Do not build a seat around a named public figure.
- **A private advisor** the user knows (a CFO, a former boss, a top customer). The user supplies the positions and heuristics. Interview the user to fill the template; never invent views for a real person.

---

```markdown
# [Role or Advisor Name]

**Lens:** [One sentence: the distinct way this seat sees marketing problems.]

## Frameworks

- **[Framework name]**: [1-2 sentence working definition, in plain words.]
- 3-6 total.

## Default positions this seat argues

- [A strong position the seat holds]
- 4-6 total. Include at least one unpopular position; a seat with no
  unpopular opinions produces no useful disagreement.

## Signature questions

- [A question this seat asks of any marketing problem]
- 3-5 total. These open the seat's take.

## Best for / blind spots

**Best for:** [problem types the lens illuminates]
**Blind spots:** [where the lens fails; this keeps its dissent honest]

## Voice notes

[2-3 sentences on rhythm, tone, and habits.]

## Natural opponents

[Which bench roles this seat tends to argue with, and why.]
```

---

**Seating a custom advisor:** name them when convening ("seat our CFO on this"). The agent loads the file from `.agents/advisors/` and applies the same grounding rules as the built-in bench.
