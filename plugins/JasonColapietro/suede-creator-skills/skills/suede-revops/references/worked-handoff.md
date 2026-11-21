# Suede AI Revenue Operations Skills: Worked Handoff

## Inputs

Request: “Fix leads getting lost between marketing and sales.” Supply a CRM
field export, lifecycle definitions, an ownership roster, available working
hours, current assignment rules, and a dated sample of handoffs. Synthetic
failure: the segment is known, but the named owner is unavailable and no fallback
queue is defined. No authority to alter production records is included.

## Expected output

Return a lifecycle definition sheet, routing decision table, SLA proposal,
implementation build list, and dashboard spec. The decision table has ordered
conditions, owner or queue, fallback, notification, timestamp, and escalation.
For the unavailable-owner case, route the proposed rule to the team's existing
fallback queue if one exists; otherwise leave a named decision for its owner.
Define time-to-assignment from a specific event timestamp and report business
hours, timezone, exclusions, and denominator. Separate fit from engagement scores.

## Failure case

A lead matches two regions, lacks an account ID, or has no consent basis for
follow-up. Specify a review queue and reason; do not guess territory ownership,
merge identities, or trigger outreach. If the sample lacks a handoff timestamp,
report SLA measurement unavailable rather than estimating response speed.

## Validation

Dry-run the table on a normal lead, missing region, duplicate account, unavailable
owner, and outside-hours arrival. Each case must resolve to exactly one proposed
route or explicit review state. Check that the CRM schema supports every field,
the build list has an owner and rollback plan, and no production mutation is
represented as complete.
