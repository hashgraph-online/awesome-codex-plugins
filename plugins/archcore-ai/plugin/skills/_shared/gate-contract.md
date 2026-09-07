# Gate Contract — Gate Record Template and Track State Rules

Plugin runtime asset. Loaded by skills (`plan`, `document`, `review`) before
executing a track gate. Also the authoring contract for track files under
`skills/_shared/tracks/`. Routing-signal order and track selection live in the
executing skills, not in this file.

## Track files

- A track file lives at `skills/_shared/tracks/<track-id>.md`.
- Each gate is one section with the heading `### gate: <track>.<stage>`.

## Gate record template

A gate record carries these fields in this fixed order. When adding a gate,
copy this template:

```markdown
### gate: <track>.<stage>

- Purpose: <the one outcome this gate settles>
- Entry conditions:
  - skip_when: <condition under which the executing skill skips this gate>
  - <condition that existing documents or the request text can satisfy>
- Elicitation knobs:
  - trigger: <condition that opens an interview at this gate>
  - taxonomy: <coverage categories from skills/_shared/coverage-taxonomy.md>
  - budget: <maximum questions at this gate>
- Produces:
  - type: <archcore document type>
  - status: draft
  - relations: <relation type and target, or none>
- Exit checks:
  - blocking: <objectively verifiable check>
  - advisory: <objectively verifiable check>
- Next: <next stage, branch conditions, or exit>
```

## Example gate

Non-normative example with placeholder names — live gates stay in their track
files, never copied here.

```markdown
### gate: track.classify

- Purpose: Select the branch this track takes.
- Entry conditions:
  - skip_when: the request names the target branch.
  - The request describes one subject for this track.
- Elicitation knobs:
  - trigger: the request does not settle the branch choice.
  - taxonomy: Constraints & Tradeoffs from `skills/_shared/coverage-taxonomy.md`.
  - budget: 1
- Produces: none — a later gate produces the document.
- Exit checks:
  - blocking: the recorded outcome names one branch gate.
- Next: `track.branch-a` when the choice is settled; `track.branch-b` otherwise.
```

## Track state block

The executing skill records track state as one HTML comment inside the draft
artifact, identified by the marker `archcore:track`:

```markdown
<!-- archcore:track
track: <track-id>
gate: <track>.<stage>
route: <computed route and size label per skills/_shared/delta-routing.md>
delta: <declared Δ fields per skills/_shared/delta-routing.md>
taxonomy: <coverage categories already covered by accepted answers>
asked: <questions already asked in this track>
budget: <remaining question budget per skills/_shared/elicitation-contract.md>
deferred: <questions deferred to a later gate>
-->
```

The `route` and `delta` fields are written by the `plan` skill's conductor
(`skills/_shared/delta-routing.md`); a skill that runs a track outside a
computed route omits both fields. A `plan`-skill resume that finds them
absent follows the conductor's resume rules; every other skill resumes per
this file alone.

### State lifecycle

1. The draft artifact is the only carrier of track state.
2. The executing skill MUST NOT hold track state in session memory or in a side file.
3. WHEN a gate closes, the executing skill MUST persist accepted answers and the state block in one `update_document` call.
4. WHEN all blocking exit checks pass, the executing skill MUST advance the `gate` field to the next stage.
5. WHEN the track exits, the executing skill MUST remove the state block from the artifact.

## Execution rules at a gate

1. WHEN a gate opens, the executing skill MUST evaluate `skip_when` before any other gate step.
2. WHEN existing documents or the request text satisfy a gate's entry conditions, the executing skill MUST ask zero questions at that gate.
3. WHEN a gate produces a document, the executing skill MUST create it with `status: draft` via `create_document`.
4. WHEN a gate produces a document, the executing skill MUST check the draft against Rules 1, 7, and 8 of `skills/_shared/precision-rules.md`.
5. IF the draft departs from those rules, THEN the executing skill MUST report each departure as an advisory finding.
6. IF an advisory exit check fails, THEN the executing skill MUST report the finding.
7. IF an advisory exit check fails, THEN the executing skill MUST proceed to the next gate.
8. IF a blocking exit check fails, THEN the executing skill MUST stop at the current gate.
9. IF a blocking exit check fails, THEN the executing skill MUST report the failed check.
10. WHEN a gate's `skip_when` holds, the executing skill MUST continue at the gate that gate's `Next` field names, unless the skip_when text itself states a different route — `skip_when` skips one gate, never the track.

Rules 4 and 5 are why no gate carries a prose check of its own: the forbidden
lexicon, the line form a type takes, and the open-list prohibition bind every
produced document, and authoring rule 5 below forbids restating a shared
contract inside a gate. A gate states only what is specific to it.

## Resume rules

1. WHEN a skill opens a draft that carries a state block, the skill MUST resume at the earliest gate whose exit checks have not passed.
2. WHILE resuming, the executing skill MUST NOT re-ask a question recorded in `asked` or answered under `## Clarifications`.
3. IF the state block names a stage absent from the track file, THEN the executing skill MUST resume at the first gate whose entry conditions fail.
4. IF the state block names a stage absent from the track file, THEN the executing skill MUST preserve recorded clarifications.
5. IF an upstream document required by an entry condition is missing, THEN the executing skill MUST route to the earliest gate that produces it.

## Authoring rules for track files

1. The track author MUST keep the gate record fields in the template order.
2. The track author MUST declare `skip_when` in every gate.
3. The track author MUST tag every exit check `blocking` or `advisory`.
4. The track author MUST reference a shared contract by path.
5. The track author MUST NOT restate a shared contract's rules inside a gate.
6. IF a gate produces no document, THEN the track author MUST write `- Produces: none` in place of the three subfields. [assumption]

Shared contract paths: interview mechanics — `skills/_shared/elicitation-contract.md`;
coverage categories — `skills/_shared/coverage-taxonomy.md`.
