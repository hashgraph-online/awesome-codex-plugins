# Suede AI Video Skills: Worked Handoff

## Inputs

Request: “Turn this demo into a short video.” Supply a product recording,
approved product facts, intended audience/action, destination, target duration,
brand assets, and rights for voice, footage, and audio. Synthetic constraint:
the host can read the recording and timecodes but has no renderer or generator.

## Expected output

Return the exact manual-handoff headings from the main skill: Script, Shot List,
Asset Manifest, Beat Sheet, Captions, Edit Decision List, Export Settings, Open
Gates. Use `edit-anatomy.md` for the beat-sheet schema. For example, a product
step at source 00:12–00:18 becomes a six-second shot with its observed action,
approved overlay, caption text, transition, and audio entry. Preserve source
timecodes separately from final placement. Mark export requirements verified
only after checking the current destination specification.

## Failure case

Unavailable rendering tools mean a plan was produced, not a video. Missing
speaker consent prevents an avatar or cloned-voice production path; offer the
documented available alternative without purchasing a tool. Missing audio rights
leaves an open asset gate, not a stock-track recommendation assumed licensed.

## Validation

Sum final shot durations, confirm every source in/out exists, and check captions
against the actual speech. Inspect aspect ratio, crop, safe areas, legibility,
audio levels, and destination settings on any returned render. If only the
manual handoff exists, report those render checks as pending. No output state
may imply generated, rendered, uploaded, or published media without that action.
