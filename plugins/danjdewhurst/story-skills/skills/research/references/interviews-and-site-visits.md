# Interviews and Site Visits

People and places answer questions no book can: what a job smells like,
what a nurse says under her breath, how long the walk from the car park
really takes. Record them as research notes with `method: interview`,
`method: site-visit`, or `method: expert-review`.

```shell
story add research 'Night shift on a cardiac ward' --method interview \
  --accuracy must-be-accurate --risk medical --used-in chapter-07
```

## Preparing an interview

1. Write the note's `## Question` first: what the chapters need.
2. Draft 8 to 12 open questions under `## Interview Plan`. Start broad
   ("Walk me through a typical night"), then specific ("What happens in
   the first five minutes of a cardiac arrest call?"). Ask for sensory
   detail, routine, jargon, and what outsiders get wrong.
3. Avoid leading questions that confirm the plot ("Would a nurse ever
   hide a death?"). Ask how things work and let the story fit the answers.
4. Agree the terms before the conversation:
   - **Consent** to take notes or record, and how the recording is stored
   - **Attribution**: named in the acknowledgements, named by role only, or
     anonymous
   - **Review**: whether they want to see the passages that draw on them
   - Nothing confidential about patients, clients, or cases they could not
     share publicly
5. Record the agreed terms in the note body under `## Consent`.

The agent can draft questions and consent wording; the user holds the
conversation. Never contact people on the user's behalf without explicit
instruction.

## Recording an interview

```markdown
## Interview Notes

- 2026-04-12, video call, 45 min. Recorded with consent; audio kept
  locally, not in the repo.
- Interviewee: charge nurse, 14 years cardiac (anonymous by request).
- > "You hear the arrest bell before you think. Your feet are already
  > moving." (00:12:40)
- Handover at 07:30 takes about 40 minutes; night staff rarely leave on
  time.
- Would not say what drugs are given first; follow up with a published
  protocol instead.
```

Give each quote a timestamp or page of notes. Mark paraphrase as
paraphrase. Keep private details (names, contact details, anything they
asked to keep out) out of the repository.

## Planning a site visit

List what the chapters need from the place under `## Visit Plan`:

- Distances and walking times between the places scenes use
- Sightlines: what can be seen from where a character stands
- Sound, smell, light at the time of day and season the scene is set
- Signs, surfaces, textures, and small details only a visitor notices
- Access: what is public, what needs permission, what has changed since
  the story's era

Check opening hours and permission before going, and photograph only where
allowed.

## Recording a site visit

```markdown
## Visit Notes

- 2026-05-03, 06:10-08:00, spring tide, overcast.
- Minsterworth bank to the church lych-gate: 7 minutes' walk.
- The bore is heard about 90 seconds before it is seen.
- Photos: 14, kept in the user's archive (not the repo).
```

Record walking or travel times on the location's `routes` as well, so
`story continuity` can check travel between scenes (see the
`worldbuilding` skill).

## Expert review

An expert review is a reading of drafted passages, not an interview. Use
`method: expert-review` for the note, list the chapter ids read in
`used-in` (it takes chapter ids only, such as `chapter-07`; name the
specific passages under `## Findings`), record the reviewer in the
`reviewed-by` list, and log their corrections under `## Findings`. Triage the notes with the `feedback-triage` skill.
Notes with a `risk` need this review before the chapters are final.

After adding or updating interview, visit, or review notes, run
`story reindex .`, `story wordcount . --write`, and `story check .`.
