# Play it on one clock

design-motion's own instructions. Read `shared/core.md` first, then `shared/decisions.md`
(the record, including the motion file format) and `shared/board.md` (every candidate is a
board page). Read `references/choreography.md` when choosing candidates and
`references/libraries.md` before building the first specimen. Paths like
`references/choreography.md` are relative to this file; `shared/` is the plugin's shared
folder (`shared/core.md`, Paths).

## What this skill does

It decides how one moment moves, in the order a motion designer works: purpose first,
then which element moves when, then the character of the movement, its timing, what
triggers and interrupts it, and the reduced version. One moment per session, one
decision per sheet section.

- **It writes no code.** A pick ends in a `기록 지시:` block to `motion-<moment>.md`.
  Building it is ordinary coding; the agent block makes it follow the record.
- **The real library plays it.** GSAP or Motion, whichever the project uses
  (`references/libraries.md`). Never a CSS imitation of a library's motion.
- **Not a single CSS value.** A request that is one CSS transition's duration or easing
  (a hover, a button press) belongs to design-helper: say so in one line and offer to
  continue here only if the moment involves more than one element or the library. The
  record's motion tokens (design-system) are used first; a value outside them reads
  `새 값` in the cost slot. With no motion tokens in the record, say so once in the
  description and leave the chip off.
- **It names what comes next**, in the order below. The user may jump, skip or stop.

## The steps

| step | decides | how |
|---|---|---|
| 1 순간과 목적 | which moment; what the motion is for (where it came from, that something changed, attention, expression); how often people see it, so productive (short, quiet) or expressive | conversation |
| 2 지금 움직임 | what the moment does today | conversation, with its frame strip |
| 3 안무 | which element moves when: together, one after another, handed over, overlapping | sheet |
| 4 성격 | the ease family or spring | sheet |
| 5 시간 | total length and the gap between elements | sheet, a ladder |
| 6 트리거와 끊김 | play once, follow the scroll, reverse; what a second trigger mid-way does | sheet |
| 7 움직임 줄이기 | the reduced version | sheet, never skipped |

Big before small: the order of elements is chosen before their curve, the curve before
the milliseconds. A later step never reopens an earlier one silently.

**Steps 1 and 2 are settled by an explicit yes**, the same way design-ux settles its first
two: inferred from the code and the request, one line each on the first sheet (`dh-list`)
and in the report, recorded when the user confirms. A pick that doesn't answer them is
recorded with them as `초안`, and the report asks again. The library goes on the step 1
line (`라이브러리: GSAP 3.15`); only a library chosen in conversation because the project
has none also goes to `README.md` `구현 방침` (`references/libraries.md`, No library yet).

**Where to start** follows the request: `카드 등장 순서` starts at 3, `튕기는 느낌` at 4,
`더 빠르게` at 5, `스크롤 따라오게` at 6. A request naming several steps starts at the
earliest and the report lists the rest in order. Steps 1 and 2 are never skipped, only
shortened. Step 2's frame strip is the one under `A 지금` in the first section. A step the
session started past stays out of the record until the end, when it is `보류`.

**Step 7 can't be skipped.** When the user ends before it, draw the reduced version of
the chosen motion with one alternative and ask for a pick in the same report; keep the
workspace until that reply. Steps left open at the end are recorded as `보류`. A reduced
specimen is the same page loaded with `#reduced` in its URL (`dhMotion.reduced`).

**After a pick**, the report names the next step; draw it when the user goes on or names
another. Letters restart at A for each step and continue when a step's ladder is appended.

## Starting

1. **The record.** A Notion page named in your first message, else `design-decisions/`.
   Read `README.md`, any `motion-<moment>.md` for this moment, `motion.md` (design-system's
   tokens) and the area files the board uses. Name the workspace `design-motion.XXXXXX`.
2. **The library.** `rg -o '"(gsap|motion|framer-motion)"' package.json`, then how the
   moment is animated today. `references/libraries.md` says how to load it in a specimen.
3. **The current motion.** When the moment exists, rebuild it as specimen `A 지금` with the
   library and values from the code, and measure it (below) for step 2. `A 지금` keeps all
   of the code's values, so it differs in more than the step's decision: its caption names
   the rest on a `다른 점` line (`곡선 power1.out, 한 요소 500ms`). When the moment doesn't
   exist, say so in one line.
   The version is the installed one, else the lockfile's, else the newest that satisfies
   the `package.json` range (`npm pack "gsap@^3.15.0"`); the caption names it.
4. **The kit.** Besides the files `shared/liveview.md` copies, copy `motion.js` and
   `motion.cjs` from `shared/assets/` into `$WS`.

## Specimens

Each candidate is a board page (`shared/board.md`): `$WS/<section id>/proto-<letter>.html`,
the project's stylesheets copied in, the real elements of the moment with real content,
settled values applied, at real size.

- **Crop to the moment.** A specimen is the region that moves plus the still parts right
  around it (a dashboard's title, toolbar and cards, not the whole page), wrapped in one
  element the measurement clips to (`<div class="moment">`). Keep it 520px wide or less
  when the moment allows, so two specimens sit side by side at 1440. A wider moment is
  drawn one per row. Either way the graph and strip make each cell tall, so on a motion
  sheet `firstScreen` below `primarySpecs` is expected; the bar is sticky for that reason.

- **Only the decision being made differs.** Steps not decided yet are held at the
  plainest choice (`references/choreography.md`, Held constant), named once in the
  section description as held, not chosen.
- **Connect the animation** with `../motion.js` so the sheet and the measurement can
  drive it: `dhMotion.gsap(tl, { track })` or `dhMotion.motion(controls, { track })`.
  `track` names the elements that move. From step 7 on, branch on `dhMotion.reduced` for
  the reduced version (`references/libraries.md`); before it there is no reduced branch.
- **Fixed overlays** (a panel or dialog with `position: fixed`) become `position: absolute`
  inside the clipped wrapper, said once in `실물과 다름`.
- **A ladder moves only the element the decision is about.** In a timing ladder for a
  panel, its backdrop keeps the code's length, named as held.
- **The sheet.** Put `<div class="dh-play" data-for="<section id>"></div>` between the
  description and the grid, and `<script src="motion.js"></script>` above `dh:script`
  once. Each specimen is an iframe at its real size. The bar plays every specimen of the
  section on one clock and slows them together, so their differences stay.
- **`실물과 다름`** once in the section description, with what is imitated: the data
  arriving, a React component mounting (`AnimatePresence`), a route change.
- **Interruption** (step 6) is drawn on one seekable clock: the specimen computes the
  whole path with the library's own math before connecting (`references/libraries.md`,
  Interruption), marks the moment of the second trigger on screen (`닫기 누름`), and
  connects through `dhMotion.custom`. A round trip starts and ends in the same place, so
  its facts are `turnAt` (how soon it reverses), `settle` (until it is gone) and `maxStep`
  (the largest move per step: a jump shows here), not overshoot or p90.
- **Scroll-linked specimens** keep the whole page at a fixed window size (the scroll room
  and the `start`/`end` percentages depend on it), shown in an iframe marked `data-window`
  of that size, named once in `실물과 다름` (`창 520×720으로 고정`). They connect through
  `dhMotion.journey` (`references/libraries.md`, Scroll), so the bar plays the same scroll
  path in every specimen, and the person can also scroll inside each one by hand. Captions
  add `seenAt` and `replays` (`아래 줄은 반쯤 보일 때 94% 진행 · 다시 내려도 재생 안 함`).

## Measuring

`motion.cjs` moves each specimen's own animation to fixed times and reads what the
library drew:

    node "$WS/motion.cjs" http://localhost:8765/r3-1/proto-B.html "$WS/r3-1/m" \
      --name B --clip .moment --width 520 --height 400 --span 900 --frames 0,100,200,300,500,end

- `--width` and `--height` are the specimen's iframe size, so the page lays out as on the
  sheet.

- Give every specimen of a section the same `--span` (the longest duration) and the same
  `--frames`, so the graphs and strips line up. Choose the frames to include the moments
  that differ: the largest overshoot (`peakAt`), the slowest specimen's `p90`. Drop a
  numbered frame equal to `end`; label the end frame `<ms>ms (끝)`.
- Read the decided element's own line in `each` (start, p90, settle, maxStep, turnAt);
  the overall values are the latest over every tracked element. Elements of one selector
  share a color, so lines that move together draw as one: say so under the graph once.
- Under each specimen: the progress graph (`<name>-graph.svg`, one color per tracked
  selector with a legend) and the frame strip: the screenshots in order, each labelled with
  its time, each at least a third of the clip's width and linked to its full PNG. A frame
  marked `pastEnd` is labelled `끝`. Images load eagerly (no `loading="lazy"`).
- The report gives `duration`, `settle`, `p90`, `overshoot`, `starts` and `spread` (when
  each element starts), `concurrent`, `layout` and `reduced` (`duration`, `travel`).
- `check.cjs` on a motion sheet checks layout and clipping. It waits for the bars, and the
  specimens rest at their end state; motion values come from `motion.cjs`, not `--props`.

## Captions

Measured facts and judgments are kept apart.

- **Facts**, on the values line: `전체 620ms · 거의 멈춤 580ms · 90% 도달 380ms · 넘침 0px`,
  and in step 3 the start spread (`시작 간격 0부터 340ms`), which is what tells orders apart.
  `layout` not empty: `레이아웃을 흔듦 (.panel 폭)`, a cost, shown even when it looks fine.
  The reduced travel is a fact only in step 7 and after; before that it is left off.
- **Judgments**, one line labelled `판단`: whether it fits the purpose from step 1 (a
  productive moment that runs long or bounces, an order that leads the eye away from
  what matters). `없음` when none.
- **What the eye sees at 1x**, in the usual one or two sentences. Differences that show
  only slowed down are said as such (`0.25배에서만 보이는 차이입니다`).
- Gains and losses as usual (`shared/writing.md`, The caption).

The recommendation weighs the purpose first, then the facts. Decide at 1x; the slow
speeds are for seeing the difference, and the recommendation says if one is invisible at
1x.

## Reading the response

| response | do |
|---|---|
| no identifiable candidate (`좋네`) | ask which one, or what to refine |
| a refinement (`B인데 조금 더 빠르게`) | append a section, letters continue |
| a pick (`B로 갈게`) | record it (below) |
| `건너뛰기`, `나중에` | record the step as `보류`; step 7 can't be |
| another step named | that step is the next order |

## Recording a pick

1. Screenshot the section with its strips (`check.cjs ... --section <id>`).
2. End with a `기록 지시:` block (`shared/decisions.md`) for `motion-<moment>.md`: the
   step's row in `결정`, the rows it fills in `사양`, a D entry with the measured facts and
   the judgment line, the screenshot. The first pick creates the file with steps 1 and 2.
3. **When step 3 (안무) is picked**, or at the first pick when the session started past
   step 3, propose `완료 조건` from what was measured (`전체 700ms 이내`,
   `transform과 opacity만`), marked `초안`, confirmed in chat. Until then `verify` is `[]`. The reduced line
   (`줄인 판 이동 0px`) joins when step 7 is picked.
   A 사양 cell whose value comes from the code, not a pick, says so (`y 20→0 (지금 코드)`).
4. **When step 7 is picked**, the block also writes `기준 코드`: the chosen motion as a
   short snippet in the project's library, with the reduced branch. It is a reference,
   not an apply. Steps left `보류` use their held values, named in a line above the code.
5. The report says, in Korean: what was settled, where it was written, and the next step.

## Ending

When the user says it is done (`끝났어`, `됐어`), make sure step 7 was settled (above),
list the steps still open in one line, then tear down as `shared/liveview.md` says.
