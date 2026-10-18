# Punch list: severity, action and decisions

Load when you write the punch list of the `figma-slop-check` skill, or when the user accepts or rejects one of its items. Covers how bad a finding is, what happens to it, where the expected value comes from, what to leave out, and how a decision is remembered for the next run.

Each finding carries two labels. **Severity** ranks it. **Action** says what happens next.

## Severity

| Level | What lands here |
| --- | --- |
| Critical | A node 1px wide or 0px tall; the screenshot step skipped; anything the Severity scoring table of [`figma-canon/references/ai-slop-signatures.md`](../../figma-canon/references/ai-slop-signatures.md) rates Critical (WCAG auto-fails, default Figma names) |
| High | A written rule broken: a raw hex where the variable exists, a glossary term changed, a value off the scale, a detached copy |
| Medium | Siblings that disagree: off by one, case that varies, an icon at two sizes |
| Low | Drift that does not change the render, such as a layer name outside the convention on a frame that looks right |

The five auto-fails of [`figma-canon/references/quality-rubric.md`](../../figma-canon/references/quality-rubric.md) (hardcoded colors, missing auto layout, default names, detached components, overlap) block a PASS whatever their severity.

List findings from the highest level down.

## Action: swap, snap or ask

Ask one question: if the found value is replaced with the expected one, does anything change on screen?

- **swap:** nothing changes. The expected value is identical to the found one and is only unbound or unapplied, such as a raw `#16181D` where `color/surface/card` holds `#16181D`. Fix it. Distance 0.
- **snap:** something moves. The found value is not a step, so it goes to the nearest step, such as padding `14` on a `12 16` scale. Fix it and log the distance, found minus expected: `+2`.
- **ask:** there is no right value to move to, because no source covers the case. Fix nothing. Put the question to the designer in the punch list.

A `14` beside siblings at `12` is a snap, not a swap. The siblings tell you where to move; they do not erase the 2px the screen had.

When a check says "report as ask" (an undecided card radius, an icon stroke width the canon never fixed), the finding goes into the punch list with the action ask and the question spelled out. Never turn it into a footer note, and never fix it quietly. A finding the canon does settle (an element that is only sometimes an instance of an existing component) takes swap or snap like any other.

Without the action, every finding defaults to "fix it". A snap that leaves no number is debt that disappears, and an ask fixed without a decision makes an undecided file look like a system.

Distances are signed and in the unit of the check (px, pt, count). Never add them up: units differ and opposite signs cancel. The summary carries the number of snaps and the largest absolute distance.

## Where the expected value comes from

Point every finding at the place its expected value is written, in this order:

1. The file's variables and styles, which are what the file actually uses.
2. The project's machine-readable token and component registries, if it has them.
3. The project map (`figma-map.md`) and design docs: scales, components and variants, glossary, voice, layer convention. With no layer convention of its own, cite [`figma-canon/references/naming-canon.md`](../../figma-canon/references/naming-canon.md).

When two sources disagree, settle it before you report. For a live component count, call `figma_get_design_system_summary` instead of quoting a doc. If the project keeps a list of resolved or known issues, read it first. If no source covers the case, the action is ask.

## Before you report

- Look at at least 2 siblings of the same kind before calling something slop or inconsistent (the Sibling-check rule in [`figma-canon/references/ai-slop-signatures.md`](../../figma-canon/references/ai-slop-signatures.md)). The flagged item is often the rule.
- Placeholder or demo copy does not break the glossary. Check whether the screen is a placeholder.
- On a frame whose name ends in `/wip` or `/draft`, token findings drop from high to medium.
- A component spec may need many fields. The density check is for meta cards about a flow.
- The user's request changes the checks: "detailed", "complete" or "exhaustive" turns the density check off; asking for a summary turns the trailing summary check off; a pull request document allows markdown headers.
- A value the user just called deliberate ("17 here because of X") is accepted once. If it comes back, record it as intentional (next section).

## Decisions file

Keep one file per project: `.figma-slop-check/decisions.json`, created on the first entry as `{ "version": 1, "entries": [] }`. An entry is one of two kinds, and the difference is the point:

| | `intentional` | `debt` |
| --- | --- | --- |
| Means | The deviation is the project's own rule | A known gap the user chose to leave for now |
| Next run | The finding leaves the punch list; a footer line counts it | The finding comes back, with its distance, until it is fixed |
| Required | `reason` and a node scope | `distance` and a node scope |

Recording debt as intentional turns a backlog into an amnesty.

An entry:

```json
{
  "id": "d-001",
  "kind": "intentional",
  "check": "scale",
  "node": { "id": "123:456", "path": "01-home / hero / btn-primary" },
  "found": "padding T17 R16 B17 L16",
  "expected": "spacing scale 4 8 12 16 24 32",
  "reason": "Optical correction for the cap height of the hero label.",
  "date": "2026-10-05",
  "until": null
}
```

- **id:** `d-001`, `d-002` and so on, in order. The user revokes by id.
- **check:** the check name from `references/checks.md`, exactly.
- **node:** `id` matches one node; `path` (names joined by ` / `) matches any node with that ancestry. `id` wins when both are set. Refuse an entry with neither: it would silence the check everywhere.
- **found / expected:** matched against the text of the finding as substrings.
- **reason:** required for `intentional`. "Looks fine" is not a reason; refuse it.
- **distance:** required for `debt`, signed.
- **until:** an optional date after which the entry is ignored. Set it for a tolerance during a redesign, and revisit anything older than about six months.

How the entries get there:

- The user calls a finding deliberate: append an `intentional` entry and tell them its id.
- The user says "later" or "leave it" on a finding: append a `debt` entry.
- The user approves a snap: apply it and add `{ check, node, found, expected, distance }` to the `fixes` list of the run file in `.figma-slop-check/runs/`. The fix is done, and the change still leaves a trail.
- "Remove d-003" deletes that entry outright.

When a run starts, load the file if it exists, drop expired entries, and match each finding against the `intentional` ones. Footer line for what was left out: `Left out by decisions.json: N findings (d-001, d-007). Say "show them" to list them.`

Never write these entries into a file that another tool generates: its next run overwrites them and the record is gone. Another tool may read `decisions.json`; only this skill writes to it.
