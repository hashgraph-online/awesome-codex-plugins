# The review folder's records

Read this before writing a review folder for the first time. The folder is the review's memory: anyone (the user, a
later session, another agent) should be able to pick the review up from it without the conversation.

## `review.md`: the index

Only the coordinating agent edits it. Read the current contents before every edit and keep any edits the user made; if
an edit of theirs conflicts with yours, ask. Keep it short:

- the PR URL and number (once they exist), canonical repository, head and base branches, the local workspace and any
  difference between it and the review target
- the overview's head SHA and comparison base, the latest head and base you observed, and when
- when you last read PR feedback, with links and any access limits
- an area table: ID and link, who investigated it, investigation state, human review state, examined head, blockers
- a candidate index: ID, link to its area, disposition, and any ticket that already covers it
- accepted findings: ID, link to the wording file, delivery state, resolution state, posted URLs
- deliveries: body file, included findings, destination and anchors, approval state, posted URLs
- pending decisions, dependencies between areas, and a short history of updates and resets

An area table in `review.md` looks like this:

```markdown
| Area | Investigated by | Investigation | Human review | Examined head |
| --- | --- | --- | --- | --- |
| [A01: State transitions](areas/A01-state-transitions.md) | coordinator | ready | pending | `<sha>` |
| [A02: Failure recovery](areas/A02-failure-recovery.md) | investigator | active | pending | `<sha>` |
```

## `overview.md`: shared context

Enough for an investigator who hasn't seen the conversation:

- the ticket's intent, acceptance criteria, constraints and non-goals
- **Current target:** the head SHA, comparison base and snapshot ID (or "committed only") investigators work on now,
  plus a **Target history** of earlier targets with the date each was replaced
- what changes and why, and the existing architecture and behavior it touches
- the changed components, boundaries and dependencies, the risks, and what's unknown
- the focus areas, why each matters, and how they overlap or depend on each other
- after step 4, any area added or changed because of other reviewers' feedback, credited to its source

## Area files

Each `areas/Ann-<slug>.md` holds, in order:

1. **Brief:** scope, key questions, paths, exclusions, dependencies, links to shared context.
2. **Assignment:** workspace, head and base, who investigated it, what they could run.
3. **Investigation:** the saved handoff: examined revision and date, reasoning, evidence with `path:line` citations,
   commands and results, coverage and limitations.
4. **Candidates:** each with its stable ID, the concern, the trigger and impact, evidence, uncertainty, whether this
   change introduced it, and its disposition.
5. **Discussion and decisions:** the user's conclusions, dismissals with their reasons, deferred questions, links to
   accepted wording files.
6. **Follow-ups:** later revisions examined, other reviewers' comments cross-referenced, fix verification, new
   concerns, and conclusions that were superseded, with why.

Append follow-ups and label them; never rewrite an earlier conclusion so that it disappears. Switching to another area
never clears notes.

## Status words

Track the investigation separately from the user's decisions and from posting.

| Record | States |
| --- | --- |
| Area investigation | queued, active, paused, blocked, ready, revisiting |
| Human area review | pending, discussing, reviewed, rereview |
| Candidate disposition | open, accepted, dismissed, deferred |
| Delivery | unprepared, draft, approved, posted |
| Accepted finding's resolution | unresolved, recheck, verified, resolved |

- `ready` means ready for discussion, and you set it only after checking the handoff states its coverage and
  limitations. It doesn't mean the area is correct.
- Only the user's explicit confirmation sets `reviewed`; record the revision it covered. An area can be reviewed with
  deferred candidates still open.
- Only the user accepts, dismisses or defers a candidate. An investigator's confidence isn't acceptance.
- An interrupted investigation is `paused` or `blocked`, with the reason, never reset to `queued`.
- `verified` means an agent checked the fix; `resolved` needs the user's confirmation. A fix doesn't erase an accepted
  finding.
- Posting or dismissing one finding doesn't complete its area.

## Keeping the records tidy

- Cite code as `path:line` (or a range) with the revision it refers to, so old line numbers aren't taken for current
  ones. Put the path and range right before any copied code.
- Use relative links between review files.
- Wrap prose at 120 characters. Code, tables, URLs and paths may run longer.
- Update the records as work and decisions happen, not only when asked.
- No secrets, credentials, tokens, customer records or end users' personal data, ever.
