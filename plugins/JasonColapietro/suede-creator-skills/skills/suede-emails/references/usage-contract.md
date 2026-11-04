# Worked contract: Suede AI Lifecycle Email Skills

This is an illustrative application, not a claim of measured customer results.

## Input

Design welcome email for opted-in trial users. Activation is creating a first project; billing begins only after explicit upgrade. The available events are signup, project_created and unsubscribe.

## Expected output

Return a sequence with signup entry, project_created and unsubscribe exits, waits, time zone, exact copy and one CTA per message. Define activation conversion with an explicit cohort and window. Give the implementer an event map and suppression rules.

## Failure and validation

Replay signup twice and verify it does not create duplicate enrollment. Unsubscribe exits before every send; project creation stops setup reminders. If a required event is unavailable, document the dependency rather than pretend the automation is installed.
