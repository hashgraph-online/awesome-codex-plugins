# Optional review lenses

Apply these lenses only when they add evidence beyond the default correctness
review. Keep their findings separate so they do not hide functional defects.

## Standards lens

Compare changed code with the applicable `AGENTS.md`, contributing guide,
architecture decisions, public contracts, and established nearby patterns.

Report a finding only when:

- a documented rule or compatibility boundary is violated;
- the deviation creates a concrete maintenance, integration, or operational
  cost; and
- the finding cites the governing source.

Do not turn stylistic preference into a standard.

## Specification lens

Map the diff and tests to the ticket, specification, design, or acceptance
criteria. Look for:

- missing or partially implemented requirements;
- behavior that contradicts the stated requirement;
- unhandled edge cases named by the specification;
- scope expansion that changes a contract without approval;
- acceptance criteria with no observable verification.

Quote or cite the requirement concisely and identify the missing behavior.

## Pass structure

One reviewer can apply all relevant lenses for a small change. For a large or
high-risk change, use bounded independent passes only when the added coverage
justifies the context and coordination cost. Deduplicate at the end without
merging distinct failure mechanisms.
