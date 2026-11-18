# Freshness, conflicts, and coverage policy

This is an operational research policy, not a claim that a deployment remains safe between reviews. Apply it with the [control-verification reference](05-liquidity-control-verification.md) and [source index](00-source-index.md).

## Keep four different times

- **Published/edited:** when the author produced or revised the source. Unknown is null.
- **Retrieved:** when this corpus acquired the exact snapshot.
- **Effective:** when a mechanism/version/configuration became applicable to a particular deployment. Do not invent this from the retrieval date.
- **Observed:** the chain block/slot/time at which a read establishes a specific state. Preserve the block hash and finalized/confirmed status when available.

A current website can describe older contracts. A new repository commit may not be deployed. A current token may still belong to a legacy factory. A chain explorer can have stale or unverified ABI metadata. Keep these distinctions visible wherever they affect a conclusion.

## Evidence and contradiction handling

1. Identify whether two statements concern the same chain, factory/program, version, token, position and lifecycle phase.
2. If they differ in scope, split them into separately valid statements rather than claiming a contradiction.
3. If they share scope, preserve both short excerpts, source locators, dates and claim IDs in the conflict ledger.
4. Resolve deployment-specific behavior using code matched to that deployment and reproducible read-only state. A source repository with unverified deployment equivalence cannot overrule a live fact by itself.
5. Mark a statement disputed or unknown until the evidence actually resolves it. Do not quietly merge incompatible fee rules or phase diagrams.
6. Retain historical statements with validity boundaries and replacement relationships. Updating the skill must not erase why an earlier conclusion was made.

A low-risk response to uncertainty is a narrower claim: “The captured v2 documentation describes a permanent locker; this run did not prove deployed bytecode equivalence or every exception.” It is not “The contract should be safe.”

## Refresh triggers

Immediately refresh before a specific live assessment when any of these matter:

- factory/program/pool/hook identity;
- creator/protocol fee policy and dynamic-fee controls;
- lock/position owner, expiry, delegates, rescue and emergency paths;
- upgrade authority or proxy implementation;
- launch configuration, phase and migration destination;
- token mint/freeze/transfer restrictions;
- reserves, active range/bins, oracle observations and quote age.

Re-open research after an official release, security advisory, governance/configuration change, program update, source contradiction, or observed decode mismatch. Data-parser compatibility is part of correctness: new account fields and instruction layouts cannot be filled with assumed defaults.

## Suggested periodic review, not automatic scheduling

- Deployment-sensitive notes: inspect within seven days, and again at the time of live use.
- Official documentation inventory: monthly, including changed canonical URLs and redirects.
- Foundational explanations/math: quarterly or after an identified correction.
- Community strategies: review when their market regime, venue or implementation changes; old anecdotes do not become validated merely because they are recrawled.

These intervals are work-planning defaults. They are neither validity guarantees nor an installed cron. Obtain separate approval before adding recurring scraping, paid APIs or notifications.

## Completeness language

Use only labels supported by actual enumeration:

- **Archived local set reviewed:** every item in a stated local inventory has a disposition. This does not prove complete source coverage.
- **All accessible sources reviewed:** enumeration reached a terminal page and every original source ID was reconciled. Mention provider history caps and unavailable/deleted targets separately.
- **Allowed community sections captured:** each authorized section has an inventory, terminal pagination evidence, attachment coverage and an exact status for every item.
- **Partial:** any unknown identity, access gap, capped history, missing source, unresolved attachment or non-terminal crawl remains.

Report discovered, fetched, usable, duplicate, excluded, pending, missing, blocked and truncated by meaning. Equal totals do not replace exact-ID reconciliation. Quoted targets are not additional independently discovered sources. A successful HTTP response containing a login screen is not a usable source. A supposedly complete tool export can itself contain upstream truncation.

## Installation and revision gate

Before installing or replacing the skill:

1. Validate package metadata, local links and privacy. Upstream private unit tests, manifests and replay commands are not shipped; do not claim they ran here.
2. Replay numerical examples and inspect assumptions.
3. Resolve all local reference links and check source locators for critical claims.
4. Have a reviewer independently assess all lock/burn/removal/upgrade assurances.
5. Run the semantic acceptance prompts when an evaluation harness is available, allowing clearly stated unknowns but no fabricated certainty. Report explicitly when prompts/graders were only structurally checked, not executed.
6. Confirm raw/private data and identifiers are excluded from Git/public artifacts.
7. State unresolved scope in the source index and handoff. Install only the reviewed reference set in the intended profile; read it back afterwards.

Preserve raw evidence privately. Do not delete archives as a convenience, expose private community membership, or republish paid content without authorization.
