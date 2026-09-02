# Translation Guide

Turn product intent into one approval-ready developer execution contract. Design vocabulary must emerge from the request, repository, and operating context; never select from a fixed architecture taxonomy.

## Recover the intended reality

Identify actors, desired outcome, observable behavior, explicit constraints, and the user's definition of done. Treat compatibility, data safety, no-code, handoff, and scope restrictions as binding.

When details are missing, avoid a serial questionnaire. Infer reversible technical choices from repository evidence. Put consequential assumptions or proposed product choices into the contract so the user reviews them together. Ask early only when no safe proposal can be made without authority the user has not granted.

## Read the actual system

Trace the named behavior from its narrowest entry point. Learn the owning modules, domain state, interfaces, asynchronous paths, deployment boundaries, failure handling, and focused tests. Widen inspection only while an unresolved fact would change the user-visible outcome, semantic boundary, data safety, public contract, or required authority.

## Generate necessary design semantics

Use any engineering concept that makes the requirement precise: domain models, state machines, contracts, transactions, concurrency, consistency, queues, scheduling, caching, resilience, security, observability, migrations, testing, or another discipline. This list is illustrative, not limiting.

Every term must change a must-hold condition, material build constraint, real execution dependency, or completion check. Choose the smallest design that satisfies `must_hold`, but do not ban a component by category. A service, dependency, MCP, grader, queue, or store is valid when it is a proportionate in-scope means of delivering the approved result.

## Translate design into executable work

Build top-down:

1. Fix the outcome, in-scope and out-of-scope boundary, and must-hold behavior.
2. Map those obligations onto the smallest concrete approach that fits the current system.
3. Add `build.semantics` only for material state, failure, security, compatibility, concurrency, migration, or operational meaning.
4. Add `build.order` only where sequence affects safe completion.
5. Choose a qualitative verification profile, assign each completion condition one typed primary source, and submit only nonempty unresolved argv subsets. Choose concrete checks from repository evidence, prefer one coalesced request when practical, and never rerun a current source merely to keep every check in one batch.

An implementation agent may change low-level tactics, dependencies, tools, files, or internal sequencing without reapproval when the result remains inside the contract's outcome, boundary, must-hold behavior, material semantics, and verification commitment.

## Present the complete Guarded contract plainly

Keep the easy explanation in the canonical `plain_language` field so it remains digest-bound. At presentation time show Goal, Changes, Unchanged, and Completion checks. Keep raw JSON behind optional Technical contract details. The human view must faithfully project every material boundary, safeguard, and completion commitment.

## Execute one shot

After approval, keep the staged contract unchanged and finish within its semantic envelope. Do not create a replacement contract for an in-scope discovery, clarification, or narrowing follow-up; append its turn digest to the audit lineage. Report material technical choices in the final result.

Stop only for new authority, an uncovered irreversible or paid external action, or a necessary change to the approved outcome, user-visible behavior, boundary, must-hold condition, or verification commitment. A blocker is not permission to widen the contract silently.

Implementation is complete when every declared source is current for the final mutation revision and no managed service remains active, or failures are reported without claiming success. Reuse exact successful argv evidence in the same revision only when the protected Git tree, normalized check, execution environment, and executable fingerprint still match. Across revisions, promote it only through the optional approval-bound dependency protocol when the host closes the approved mutation snapshot and the relevant resolved path receipt is unchanged; otherwise run fresh evidence.
