# Prose And Report Workmanship

Use this reference when documentation needs to read like maintainable project material rather than agent-generated filler.

## Prose Cleanup

Remove writing artifacts that do not help the operator:

- Inflated claims without evidence.
- Repeated "not only/but also" constructions.
- Decorative punctuation or emphasis that hides the main point.
- Meta-commentary about how the document is written.
- Long setup before the command, decision, or finding.

Keep the tone direct, concrete, and source-grounded.

## Architecture Report Rules

For codebase reports:

1. Start from the user-facing or operator-facing entry points.
2. Explain the dominant flow before listing files.
3. Name invariants and contracts, not just modules.
4. Separate facts from inferences.
5. End with risks and questions that affect future work.

## Final Pass

Before publishing docs:

| Check | Pass condition |
|---|---|
| Evidence | Claims cite code, commands, or source docs. |
| Brevity | Each section earns its place. |
| Operator value | The next reader can act without rediscovery. |
| No filler | Generic AI prose is removed. |

---

**Source:** Adapted from an external skill corpus / `de-slopify` and `codebase-report`. Pattern-only, no verbatim text.
