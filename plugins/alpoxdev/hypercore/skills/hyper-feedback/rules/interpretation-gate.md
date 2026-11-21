# Interpretation Gate

> Choose the reading the evidence supports and act on it; ask only when guessing would be costly, and hand off what a direct edit cannot hold.

## 1. Outcome and Reading

For each item, write two lines before editing:

- **Outcome**: what the author is trying to achieve for their users, in one sentence. A proposed solution ("버튼을 빨간색으로") is kept as a constraint only when the author insists on it; otherwise it is one candidate for the outcome ("눈에 띄게").
- **Acceptance**: one check someone could observe after the change - a rendered string, a reachable control, a returned value, a test that would have failed before.

Choose the reading by climbing this evidence ladder and stop at the first rung that decides:

1. The request's own words and the author's stated constraints.
2. Product decisions already recorded in the repository: specs, `DESIGN.md`, `AGENTS.md`, ADRs, issue text linked from the code.
3. The repository's conventions: design tokens, copy style, component patterns, naming.
4. The nearest existing pattern that solves the same kind of problem elsewhere in the product.
5. The smallest reversible change that meets the outcome, labeled as an assumption.

Record the rung that decided each item. When rung 5 decided, the report lists the item under assumptions.

## 2. When to Ask

Ask only for one of these three reasons, and only after inspecting the repository:

1. **Material ambiguity**: two readings lead to different user-visible results, no rung of the ladder separates them, and choosing wrong would redo most of the item.
2. **Irreversible or external effect**: the item would delete data, run a destructive migration, change prices, legal or contract text, permissions, or billing behavior, or send anything outside the repository.
3. **Conflict**: two items contradict each other, or an item contradicts a product decision recorded in the repository.

How to ask:

- One decision at a time, in the user's language, with a recommended option and its reason:

```text
[결정] <what to settle>
[영향] <what changes with each choice>
[선택지] A: ... (추천) / B: ...
```

- Mark only that item `awaiting_input`; finish every other item first.
- A question the ladder can answer, a question about naming, file placement, or styling that follows the repository's conventions, or a question asked "just to be safe" is not allowed.

## 3. Direct-Edit Budget

Edit an item directly when all of these hold:

- it changes existing modules only, with no new route, module, package, or service boundary
- it needs no schema change, data migration, or backfill
- it breaks no public API contract and adds or upgrades no dependency
- it changes no authentication, authorization, payment, or billing logic (copy around them is fine)
- its steps have no ordering dependency across systems that would need staged delivery

An item that fails any line is `handoff`. Write it to `.hyper/feedback/<slug>/brief.md`, which a planning step can consume without re-reading the request:

```markdown
# <title>

- 원문: "<verbatim quote>" (출처: <author / relay>)
- 원하는 결과: <outcome>
- 수용 기준: <observable checks>
- 예산 초과 사유: <the budget line that failed>
- 확인한 위치: `path:line` - <what it does now>
- 변경 지도 초안: <surface rows from the checklist, with known locations>
- 가정·미확인: <open points>
```

Items within the budget are still applied in the same run; a handoff never holds them back.

## 4. Wording and Constraints

- Text the author wrote for end users is applied character for character, including spacing and punctuation. When it conflicts with the repository's copy rules, apply it, then note the rule it breaks in the report.
- Constraints the author stated ("나머지는 그대로") are part of the acceptance check: the residue sweep confirms the kept parts did not change.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Acting on the best-supported reading without a confirmation step, and asking only for material, costly-to-reverse choices | user instruction, 2026-11-07 |
| The decision, impact, and options question shape, and approval separated from capability | <https://github.com/alpoxdev/hypercore/blob/01be78de5973eb75a616e5156058621a6fabbc97/instructions/cli/capability-contract.md> |
| Destructive, external, and production effects gated behind explicit permission | `instructions/sourcing/references/retrieval-safety.md` §7 |
| The evidence ladder, the three ask reasons, and the direct-edit budget lines | this package's chosen design (`LOCAL`), not a validated optimum |
