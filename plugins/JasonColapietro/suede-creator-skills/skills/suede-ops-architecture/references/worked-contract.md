# Suede AI Operations Architecture Skills: Worked Contract

This is a synthetic application scenario, not a client result or a required output filename. Adapt the values to the supplied evidence. The skill's existing output format and authority boundaries apply.

## Input

An assessment identifies duplicate order entry between a storefront and a spreadsheet. Staff enter forty orders per day, exception ownership is unclear, and the buyer has not approved a new service.

## Expected output

Compare simplification and an existing-system integration before proposing new software. Return the architecture with system-of-record choice, event/data flow, exception owner, rollback path, adoption steps, staged implementation work, and the checks that establish the intended outcome.

## Missing input and recovery

If the assessment omits the process owner or baseline, keep those fields unresolved and name what is needed to make the design implementable. Do not invent a savings estimate or assume new-service approval. If a connector cannot be used, return a manual handoff path with its cost stated.

## Validation

Trace one normal order, one duplicate, and one failed transfer through the proposed flow. Check that each has a durable identifier, an accountable owner, and a recovery action. Separate requester-provided figures from agent estimates.

## Detailed scope and routing

Suede AI operations-architecture discipline that fixes the shape of a system before anyone builds it: entity schema first, exactly one write path per entity, every unit of work routed to a deterministic automation, an AI agent, or a human decision, every existing tool marked absorb, keep, or kill, and the build sequenced into phases whose completion is proved by a command. Use when scoping an automation or agent build, deciding whether a workflow needs a model at all, consolidating a sprawling tool stack, designing the data model under a workflow, choosing a migration path off an old system, or ordering a build so nothing lands on a moving foundation. NOT FOR: executing a planned multi-file repo change (use suede-graph-flo-xr); coordinating parallel builders with file ownership (use suede-agent-teams); lead lifecycle, scoring, and CRM routing rules (use suede-revops); proving agent output quality against an eval set (use suede-ai-eval); reviewing the finished diff (use suede-code).
