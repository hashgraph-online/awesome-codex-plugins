# API contract drift — finite — checked-in server, schema, and client contracts brought back into agreement

Objective mismatches between routes, schemas, generated clients, fixtures, or checked-in contracts,
found using API tooling the repository already configures. Breaking choices remain with the owner.

Supported on projects with an established contract source and comparison command: OpenAPI or
GraphQL generation/checks, protobuf or schema compilation, consumer-contract tests, generated SDK
checks, or an equivalent repository-owned gate. Without both, this shift must not start.
Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **API contract drift — align existing API artifacts without silently changing the public API.**
  - Never select this entry when work mode is artifact.
  - Discovery: identify the repository's authoritative API source and run its configured generation,
    diff, schema, compatibility, or consumer-contract command. Compare server routes, checked-in
    schemas, generated clients, fixtures, and contract tests as applicable. Dedupe findings against
    snag-log.md (ALL seen — fixed and rejected).
  - Classify each mismatch before editing: non-breaking artifact drift with an authoritative source,
    or a potentially breaking change involving removal, narrowing, renaming, required fields,
    status codes, or compatibility policy.
  - Repair non-breaking artifact drift one coherent cluster at a time from the established source
    of truth. Run the contract command and item gate, commit.
  - Park every potentially breaking change in drafting-table.md with affected consumers, evidence,
    compatibility question, and rollback path. Do not choose the public contract unattended.
  - Never silently change a public API, invent a compatibility or versioning policy, or regenerate
    from a source whose authority is unclear.
  - Never add contract tooling, accept a generated diff blindly, or update snapshots merely to
    make the comparison pass without reviewing the semantic change.
  - Ends when configured contract checks report no actionable non-breaking drift, and every
    potentially breaking mismatch is staged for owner review with evidence.
  - Verify: the item gate is green at every commit; the repository's existing generation or
    contract-comparison command is clean and relevant server/client tests pass.
```
