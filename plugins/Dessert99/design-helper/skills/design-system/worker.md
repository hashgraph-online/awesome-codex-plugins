# Build the system by eye

design-system's own instructions. Read `shared/core.md` first, then
`shared/decisions.md`: the record this skill writes. Read `references/checklist.md`
before the first sheet, and `references/imports.md` when a candidate comes from a public
design system. Paths like `references/checklist.md` are relative to this file; `shared/`
is the plugin's shared folder (`shared/core.md`, Paths).

## What this skill does

It fills the project's design decision record, one checklist item at a time. Every item
is drawn, seen and picked; every pick is recorded with its reason.

- **It writes no code.** A pick ends in a `기록 지시:` block, never `반영 지시:`.
- **It names what comes next.** Unlike design-helper, the checklist is the point: after a
  pick, the report names the next item in checklist order. The user may pick another
  item, skip one or stop at any time.
- **Nothing counts until seen.** A value from the code, a base, an import or the user's
  own words is a candidate. It becomes `확정` only when picked from a sheet
  (`shared/decisions.md`, rule 1, which also names the three rows settled in chat).

## Starting

1. **Find the record.** A Notion page named in your first message, else
   `design-decisions/` in the project. Read `README.md` and only the area files the next
   item needs. Continuing an earlier session, request numbers continue after the highest
   `요청 N` the record cites, so a screenshot reference never means two sheets.
2. **No record yet.** Detect the style system (`shared/stylesystems.md`) and read the
   current tokens. Keep them in `$WS/memo.md` as `초안` with source
   `현재 코드 (초안)`. Nothing is written to the project before the first pick. Name the
   workspace `design-system.XXXXXX`.
3. **Purpose and mood** are settled in conversation (rule 1's exception). Infer what the
   code shows (the screens, the menu) and say the inference in one line; ask only what is
   still missing, one question at a time (`shared/clarification.md`). The answers become
   the first intents, shown in the first sheet's description and recorded in `README.md`
   (`목적과 분위기`) with the first pick.
4. **The first sheet is the starting point.** Draw the board (below) as a few starting
   points side by side: the current design when there is one, two or three directions,
   and any base the user named. Directions are anchors, not a matrix: each caption names
   the properties its direction bundles (`skills/design-helper/references/sweeping.md`,
   the coordinate sweep). The pick settles the `출발점` row only. Every value it brings is
   listed in `README.md` under `출발점 값 (초안)` and stays `초안` until its own item.

## The board

Every specimen is the same board of the project's real parts: `shared/board.md` says how
to build it (one frozen page per section, variants by hash, real size). Everything
settled when a section is drawn is part of that section's board.

## One item, one ladder

- Work in checklist order (`references/checklist.md`), roles before values
  (`shared/decisions.md`, rule 5).
- **Letters restart at A for each item** and continue within it when a ladder is
  appended. When one turn draws two items, the report and the sections name each item
  with its letters (`역할 C`, `본문 크기 B`), so a bare `A` is never ambiguous; ask which
  item when a reply uses a bare letter that exists in both.
- **Candidates:** the current value, the base's value, values from public systems
  (`references/imports.md`) and free values around them. The caption's cost slot names
  the source: `현재값`, `기반 그대로`, `Radix Colors 3.0`, `임의값`, `직접 지정`.
- **A whole area at once:** the first ladder of an area may include `기반 그대로` as one
  specimen. Picking it settles every row of that area the base fills, in one decision.
- **A role split** can't be seen without values. Draw each split with the current or
  draft values for its roles, say so in the section description, and record the roles
  only: the values stay `초안` for their own items. Map roles to the project's existing
  tokens when they are size steps (`--text-sm`): the values table names the token a role
  uses.
- **A value asked for before its roles** (`본문은 15px로`, while the roles are open) is
  drawn anyway, after the roles ladder, with a one-line note on what it will govern once
  the roles are settled.
- **Intents:** an area opens with its default intents (`references/checklist.md`) in the
  section's first lines, each caption saying which intent the specimen keeps or breaks.
  The user may change an intent in chat; a changed intent is redrawn, and intents are
  recorded with the area's first pick.
- **A value stated in words** (`버튼은 8px로 둥글게`) is drawn with the current value or
  its neighbours beside it. It is recorded only when picked.
- **Visible accessibility** is measured, never asked (`check.cjs --a11y`), against WCAG
  2.2 AA (4.5:1 body text, 3:1 large text and icons, about 44px to press).
  - Caption the pairs the item changes. For a starting point or anything that changes
    the whole board, caption body text, the weakest text pair, and the primary button.
  - Read `대비 4.8:1` or `대비 부족 2.5:1`, and `누르는 영역 32×32 (기준 44)` when a
    pressable part is below it. Control borders and focus outlines are non-text: `--a11y`
    reports them as `border` and `outline`, read against 3:1
    (`테두리 대비 부족 1.3:1`). Specimens below the standard are shown, not dropped.
  - The focus indicator is an item of its own.
- **Implementation policy** (how components get keyboard and screen reader behaviour) is
  settled in chat. Offer the candidates that fit the project's stack (for React, Radix
  Primitives or Base UI; otherwise native HTML elements first) and record the answer
  with source `대화로 결정`.

## Progress on the sheet

Fill the `<!-- dh:progress -->` marker with the checklist's status (`shared/sheet.md`).
Rewrite it whenever a row changes. It shows reading position only; it is never a
control.

## Reading the response

| response | do |
|---|---|
| no identifiable specimen (`좋네`) | ask which one, or what to refine |
| a refinement (`C에서 조금 더 진하게`) | append a ladder below, letters continue |
| a pick (`C로 갈게`) | record it (below) |
| `건너뛰기`, `나중에` | record the row as `보류`, with the question it leaves |
| `필요 없어` | record the row as `해당 없음` |
| another item named | that item is the next order |

Not deciding needs no sheet; deciding always does.

## Recording a pick

1. Screenshot the section the pick came from: `check.cjs ... --section <id>` into
   `$WS/<id>.png`.
2. **The drawing is what was picked.** Before writing the block, compare the picked
   specimen with its caption. Where they differ, record what was drawn and say the
   difference to the user in one line.
3. End the final message with a `기록 지시:` block (`shared/decisions.md`, `Recording`),
   after the Korean report. A pick that settles a whole area lists every row it fills.
4. A revision archives the old entry; it never edits it in place. Draft rows in
   `README.md` are updated in place (`shared/decisions.md`).
5. Find files whose `reopen_when` matches the change and add a `다시 볼 곳:` line.
6. The report says, in Korean: what was settled, where it was written, and the next item.
7. When a `확정` value (a row whose `상태` is `확정`) now differs from the code, or the
   code has no token for it, add one line naming design-sync, once per session. A role
   settled with its value still a draft doesn't count: there is nothing to sync yet.

The main agent answers with `기록 완료:` before the next reply. Read the record again
only where it changed.

Where the code and a `확정` row differ, say it once as a finding (`shared/core.md`).
Change neither.

## Ending

When the user says it is done (`끝났어`, `됐어`), summarize what is still open by area,
one short line each with counts (`간격: 5개 남음`), then tear down as
`shared/liveview.md` says.
