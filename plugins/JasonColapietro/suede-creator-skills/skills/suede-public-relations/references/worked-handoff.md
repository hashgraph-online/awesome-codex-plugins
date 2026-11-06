# Suede AI Public Relations Skills: Worked Handoff

## Inputs

Request: “Draft a journalist pitch about our new export format.” Supply the
release note, public format specification, approved spokesperson, intended beat,
and one recent article by the journalist. The release note supports exporting
CSV and JSON; it contains no adoption, performance, or market-leadership data.

## Expected output

Return one angle tied to the journalist's actual beat, a subject line, a pitch
under 200 words, source links for each factual hook, and an available interview
or sample-file offer. A suitable core sentence is: “The new export supports CSV
and JSON; the attached specification shows the fields and a sample record.”
Explain why that matters to this beat using the supplied article, without
pretending the journalist endorsed it. Include the send-approval handover with
the proposed recipient, verified contact source, exact draft, and open questions.

## Failure case

The article is unavailable, or its author has moved beats. Do not label the
contact qualified from an old database record. Draft a beat-neutral version,
mark the recipient research incomplete, and name the one current source needed.
If no verified contact exists, deliver the draft without a guessed address.

## Validation

Count the pitch words, reopen the cited article and release note, and check that
the angle includes actual news rather than an unsupported “first” claim. Every
media-list row needs a beat source and date. Verify that nothing was sent and
that no coverage, backlink, or AI citation is reported as earned before it exists.
