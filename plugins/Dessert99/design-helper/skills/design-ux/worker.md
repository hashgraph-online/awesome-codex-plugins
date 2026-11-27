# Try the task by hand

design-ux's own instructions. Read `shared/core.md` first, then `shared/decisions.md`
(the record, including the UX file format) and `shared/board.md` (prototypes are built on
the board). Read `references/patterns.md` when choosing candidates and
`references/evaluate.md` before writing the first caption. Paths like
`references/patterns.md` are relative to this file; `shared/` is the plugin's shared
folder (`shared/core.md`, Paths).

## What this skill does

It decides how one feature works, in the order a UX designer works: from the goal down
to the words. One task per session, one decision per sheet section.

- **It writes no code.** A pick ends in a `기록 지시:` block to `ux-<task>.md`. Building
  the feature is ordinary coding; the agent block makes it follow the record.
- **It names what comes next**, in the order below. The user may jump, skip or stop.
- **Nothing counts until seen.** Steps 3 to 7 are settled only by picking from a sheet.
  Steps 1 and 2 are settled in conversation (`shared/decisions.md`, rule 1).
- **One feature, not the app.** A whole app's navigation, site map or a journey across
  features is out of scope: say so in one line and offer the part that is one task.

## The seven steps

| step | decides | how |
|---|---|---|
| 1 목표와 사용자 | who does it, in what situation, to finish what | conversation |
| 2 과제 단계 | the task from start to end: steps and decision points | conversation, with the current flow's step strip |
| 3 흐름 | how many screens the task passes, where it starts and ends | sheet |
| 4 화면 구성 | what the key screen shows first, and how it is grouped | sheet |
| 5 상호작용 | one interaction at a time (detail view, confirm, search, ...) | sheet, one pattern each |
| 6 상태 | empty, loading, error and the other states of the chosen flow | sheet |
| 7 문구 | button names, confirmations, empty and error messages | sheet |

Big before small: a flow is chosen before its buttons. A later step never reopens an
earlier one silently; if it has to, say so and treat it as a revision.

**Where to start** follows the request. A whole feature (`주문 취소 흐름 잡아줘`) starts at
1. A screen (`상세 패널에 뭘 먼저 보여 줄지`) starts at 4, an interaction
(`삭제 확인을 창으로 할지`) at 5, a state (`주문이 없을 때`) at 6, wording at 7. Steps 1
and 2 are never skipped, only shortened: infer them from the code and the record, state
them in one line each on the sheet and in the report, and ask only what changes the
answer (how often the task is done changes whether a confirm dialog helps or hinders).

**Steps 1 and 2 are settled by an explicit yes.** The first turn may draw the first
sheet with them inferred, but the report ends by asking whether the two lines are right.
They are recorded when the user confirms (in the same reply as a pick is fine); silence
or a pick that ignores them doesn't settle them. A correction that changes the task
redraws the sheet. A requirement the user adds in words belongs to step 2 when it
changes what the task does (`거절할 때 사유를 남길 수 있다`), and to a later step when it
changes how (`사유는 입력 칸으로`): the second kind is drawn there.

## Starting

1. **The record.** A Notion page named in your first message, else `design-decisions/`.
   Read `README.md`, any `ux-<task>.md` for this task, and the area files whose values the
   prototypes will use. Visual values marked `확정` are used as they are; otherwise the
   code's current look is. Name the workspace `design-ux.XXXXXX`.
2. **The current flow.** When the feature exists, build it as prototype `A 지금` from the
   code, and walk it (below) for step 2: its strip shows the steps it takes today and where
   it gets stuck. When the user gives the URL of a running app, walk that instead and say
   it is the real app. When the feature doesn't exist yet, there is no `A 지금`: say so in
   one line, and step 2 rests on the conversation alone.

## Prototypes

Each candidate is a working page: `$WS/<section id>/proto-<letter>.html`, built like the
board (`shared/board.md`): the project's stylesheets copied in, real content, the same
data in every candidate, settled values applied. A short script makes it behave.

- Only the decision being made differs between candidates. Everything settled stays.
- **Later steps not decided yet are held constant** with the plainest behaviour that lets
  the task finish (act directly, change the status in place, no dialog, no toast), the
  same in every candidate, and named once in the section description as held, not chosen.
- **A prototype is a window**: a real viewport size (for example 1080 by 700) that the page
  scrolls inside, marked `data-window` on its iframe (`shared/board.md`).
- The behaviour is imitated, not the product's code: say `실물과 다름` once in the section
  description, with what is imitated.
- Shown in the sheet as an iframe the user can click through, with the step strip beside
  or under it.
- Draw only the conditions that change the pattern (`references/patterns.md` names them
  per category): 200 rows for paging, none for an empty state. One condition per row.

## The step strip

`walk.cjs` performs the task in each prototype and screenshots every step:

    node "$WS/walk.cjs" http://localhost:8765/r3-1/proto-B.html "$WS/r3-1/strip" \
      --scenario "$WS/r3-1/scenario-B.json"

- **One scenario per candidate, the same task.** Write the path a person would take,
  each step with the selector it clicks or fills and the selector that must appear
  (`expect`). A step that fails means the prototype doesn't do what it claims: fix it
  before showing.
- **Keyboard:** add the natural key path (Tab to the target, Enter). If it doesn't finish,
  that is a finding, not a scenario to rewrite: report the focus trail it printed.
- **Readable strips.** Set the scenario's `clip` to the region where the task happens (the
  list and the panel, not the whole page), and show each shot at least 320px wide, so the
  change between steps can be read. Never shrink a full page into a thumbnail. Images in the
  sheet load eagerly (no `loading="lazy"`), or screenshots of the sheet miss them.
- Show the screenshots in order under the prototype, each labelled with its step
  (`1 목록 → 2 패널 열기 → 3 취소`). Real screenshots, never redrawn.
- **Repetition is measured, not shown.** A condition like `세 건 연달아` is walked and its
  numbers go on the caption; its strip is not drawn. Only the single run gets a strip.
- A page that scrolls as a whole uses `"list": "page"`. A keyboard path that needs a pause
  for the page to settle gets `{ "wait": 200 }`; a run that fails only without the pause is
  a timing artifact, not a finding.
- The report gives `clicks`, `inputs`, `transitions`, `listKept`, `keyboard.done` and
  `keyboard.presses`.

## Captions

Measured facts and judgments are kept apart (`references/evaluate.md`):

- **Facts**, as chips on the values line: `클릭 2 · 입력 0 · 화면 전환 0 · 목록 위치 유지 ·
  키보드로 완료 (키 19번)`. A failing one is still shown (`키보드로 완료 불가`). With a
  condition, one values line per condition, each labelled (`한 건:`, `세 건 연달아:`).
- **Walkthrough**, one line labelled `워크스루`: the step where a person would get stuck,
  and why (`2단계: 취소 버튼이 ⋯ 메뉴 안에 숨어 있음`), or that none was found.
- **Principles**, only when one is broken, labelled `원칙`: the principle's Korean name
  and the step (`되돌리기 없음: 3단계에서 취소가 바로 확정됨`).
- Gains and losses as usual (`shared/writing.md`, The caption).

The recommendation below the section weighs the facts first, then the walkthrough.

## States (step 6)

List the states the chosen flow can reach (`references/evaluate.md`, the state list) and
draw only those that apply. Each state is one row: the state's recommended treatment,
plus alternatives where the treatment is a real choice. A reply like `이대로` settles
every state drawn in that section, because each was seen.

## Accessibility

Keyboard completion and the focus trail are measured on every candidate. When the record
has an implementation policy (`동작 접근성 방침`), the prototypes imitate that library's
keyboard behaviour. Contrast and sizes follow `check.cjs --frames --a11y` as elsewhere.

## Reading the response

| response | do |
|---|---|
| no identifiable candidate (`좋네`) | ask which one, or what to refine |
| a refinement (`B인데 패널이 더 넓으면`) | append a section, letters continue |
| a pick (`B로 갈게`) | record it (below) |
| `건너뛰기`, `나중에` | record the step as `보류` |
| another step named | that step is the next order |

## Recording a pick

1. Screenshot the section, strips included (`check.cjs ... --section <id>`).
2. End with a `기록 지시:` block for `ux-<task>.md` (`shared/decisions.md`): the step's
   row in `결정`, a D entry with the measured facts and the walkthrough line, the
   screenshot. The first pick in a task creates the file with steps 1 and 2.
3. **When step 3 (흐름) is picked**, propose the task's `완료 조건` from what was measured
   (`클릭 3번 이내`, `목록 위치 유지`, `키보드만으로 완료`), in the same block, marked
   `초안`. They become `확정` when the user confirms them in chat.
4. The report says, in Korean: what was settled, where it was written, and the next step.

Where the code and a `확정` row differ, say it once as a finding. Change neither.

## Ending

When the user says it is done (`끝났어`, `됐어`), list the steps still open in one line,
then tear down as `shared/liveview.md` says. Steps never reached stay out of the file; only
a step the user chose to skip is recorded as `보류`.
