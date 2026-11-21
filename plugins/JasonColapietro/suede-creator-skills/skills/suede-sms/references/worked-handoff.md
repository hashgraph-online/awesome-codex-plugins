# Suede AI SMS Skills: Worked Handoff

## Inputs

Request: “Draft our SMS welcome flow.” Synthetic brand: Cedar. Supplied inputs
are opt-in text and capture source, recipient jurisdictions/timezones, consent
records, current registration sample, approved destination, offer terms, and a
one-segment GSM-7 budget. If those facts are unavailable, the compliance section
names the gaps before a flow recommendation. No send authority is included.

## Expected output

Use the main skill's six-section output. A sample message using a reserved
example destination is:

```text
Trigger: confirmed SMS opt-in
Delay: after confirmation, inside the verified recipient-local send window
Copy: (90 chars, 1 segment, GSM-7)
Cedar: Your welcome guide is ready: https://example.com/welcome Reply STOP to unsubscribe.
CTA link: replace with the approved tracked destination before use
Segment: valid consenting new subscribers; exclude suppressed or withdrawn consent
Compliance footer: STOP language included
```

This is a formatting exercise, not send-ready copy. The real link's full length,
tracking, personalization, and registration consistency must be checked again.

## Failure case

Missing consent, suppression status, local time, or registration evidence leaves
an open program issue. Draft the corrected requirement and owner; never import
numbers or treat email consent as SMS consent. An emoji or smart quote can alter
encoding and segment count: recalculate the exact final text rather than keeping
the sample count.

## Validation

Count the actual message including sender, URL, spaces, and opt-out text. Verify
encoding, concatenated-segment limits, approved destination, personalization
fallback, STOP/HELP handling, recipient-local timing, and registration match.
Use the user's dated delivered/send denominators for performance, without fixed
lift or LTV promises. Current legal and carrier rules require current sources.
