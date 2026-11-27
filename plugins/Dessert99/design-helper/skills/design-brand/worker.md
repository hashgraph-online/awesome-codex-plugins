# Pick it where it is used

design-brand's own instructions. Read `shared/core.md` first, then `shared/decisions.md`
(the record, including the icon and logo file formats) and `shared/board.md` (every
candidate is drawn on a board). Read `references/icons.md` before the first icon sheet
and `references/logo.md` before the first logo sheet. Paths like `references/icons.md`
are relative to this file; `shared/` is the plugin's shared folder (`shared/core.md`,
Paths).

## What this skill does

It settles a product's icon set and its logo direction, the way a brand designer works:
the brief first, broad directions next, then one attribute at a time, then the small
sizes. Every candidate is drawn on the spots where it will really appear.

- **It writes no code.** A pick ends in a `기록 지시:` block to `icons.md` or `logo.md`.
  The chosen logo files go to `design-decisions/assets/brand/` through the same block.
  Swapping the icon package or linking the favicon is ordinary coding the record guides.
- **It never imitates a brand.** See `references/logo.md`, Not like anyone else. A request
  to copy one is answered in one line, then turned into attributes.
- **It does not choose colors.** A `확정` primary color in the record is used as it is;
  without one, logos are drawn in one dark color. Color is design-system's decision.
  Whether the mark survives in one color and reversed is measured, never asked.
- **Logos are SVG only.** Never use an image generation tool for a logo or an icon, even
  when one is available: a raster image has no 16px version and can't change one
  attribute while the rest holds still. Characters and illustrations are out of scope.
- **It names what comes next**, in the order below. The user may jump, skip or stop.

## The steps

Step 1 is shared; after it the work splits into two tracks that don't depend on each
other. Start the track the user asked for; doing only one is fine.

| step | decides | how |
|---|---|---|
| 1 바탕 | name, what the product does, three personality words, where the mark appears, brands it must not resemble | conversation |
| I2 세트 | which public icon set | sheet |
| I3 굵기와 채움 | stroke width or weight; whether the selected state turns filled: two rows, two sections | sheet |
| I4 크기 | the size per spot (beside text, in a button, in the menu): one section and one row per spot | sheet |
| I5 개념별 그림 | one ambiguous concept at a time (settings: gear or sliders) | sheet, one concept each |
| L2 형식 | wordmark, lettermark, symbol, or symbol with name | sheet |
| L3 서체 | the typeface of the name | sheet |
| L4 심볼 방향 | for a symbol or combination: the idea behind the symbol | sheet |
| L5 세부 | weight, spacing, corners, symbol to name proportion: one at a time | sheet, one attribute each |
| L6 작은 판 | the simplified version for 16 and 32px | sheet |

Big before small: a form is chosen before its typeface, a typeface before its spacing.
L5 attributes the user chooses not to see are recorded as `보류` rows, one per attribute.
A later step never reopens an earlier one silently; if it has to, say so and treat it as
a revision.

**Step 1 is settled by an explicit yes.** Infer it from the code, the record and the
request; state it as five short lines on the first sheet (`dh-list`) and in the report,
and ask only what is missing. What the code and record don't say (the personality words,
brands to avoid) is asked, marked `추정` if you offer a guess; never borrow it from an
example in these instructions. A pick that doesn't answer step 1 is recorded with step 1
as `초안`, and the report asks again. The first turn may draw the first sheet with step 1 inferred; it is
recorded when the user confirms (in the same reply as a pick is fine). A brand the user
names as one to avoid goes on the list; it never becomes a reference to draw from.

Step 1's `쓰이는 자리` line is per track: when the second track starts, restate only that
line for it and ask whether it is right; the rest stands.

A section whose decision touches one spot (the selected fill, one concept's drawing) draws
that spot only. Steps that don't depend on each other may be drawn in the same turn when
the request names them all.

**Where to start** follows the request: `아이콘 세트 골라줘` starts at I2, `로고 만들어줘`
at L2, `파비콘이 뭉개져` at L6, `설정 아이콘이 애매해` at I5. Step 1 is never skipped,
only shortened.

## Starting

1. **The record.** A Notion page named in your first message, else `design-decisions/`.
   Read `README.md`, `icons.md` and `logo.md` if they exist, and the color and typography
   files whose values the boards will use. Name the workspace `design-brand.XXXXXX`.
2. **What exists.** Icons in use: the icon package in `package.json` and the names
   imported across the code. A logo or favicon: `public/`, `static/`, `assets/` and the
   `<link rel="icon">` in the HTML. Fonts the project already loads. An existing set or
   logo becomes candidate `A 지금`. The import lines carry the names:
   `rg -n "from '(lucide-react|@phosphor-icons/react|@tabler/icons-react|@heroicons/react[^']*)'"`.
3. **The kit.** Besides the files `shared/liveview.md` copies, copy `icons.cjs` and
   `pixel.cjs` from `shared/assets/` into `$WS`.

## The spots board

Every candidate is one board of spots (`shared/board.md`): the project's own stylesheets,
its real header, buttons, table and empty state where they exist, real sizes. Icon spots
the project doesn't have are left out. Logo spots: the headers, the tab at 16 and 32, the
enlargement and the dark strip are always drawn; the app icon and the profile picture
only when step 1 names them. With no mobile header, narrow the real one to 360, hide its
navigation and add a menu button with the project's icon button class.

| track | spots |
|---|---|
| icons | the menu (with labels), a button with a label, an icon-only button, table row actions, a status mark beside text, an empty state (48 or larger) |
| logo | desktop header, 360px mobile header with the menu button (the real header narrowed when the project has no mobile one), the browser tab at 16px with the page title, the same 16px enlarged 8 times (from `pixel.cjs`), 32px, a 180px app icon, a round profile picture, a dark strip (reversed, always) |

- **Same content in every candidate.** The same concepts, labels, rows and name.
- **Steps not decided yet are held constant** with the plainest choice, the same in every
  candidate, and named once in the section description as held, not chosen: the set's
  default weight before I3, the current sizes before I4, one plain shape before L4, and
  before L3 the project's body typeface when it has a font file, otherwise Pretendard
  (Korean) or Inter (Latin), named as a stand-in.
- **The reversed spot is always drawn** for logos, even when the project has no dark
  surface: one dark strip, measured for contrast, so one-color and reversed use is known.
- **Draw logos with `currentColor` and real holes.** A cutout is a hole in the shape
  (`fill-rule="evenodd"` or a mask), never white paint, so the reversed and one-color
  versions come from CSS color alone and the mark works on any background.
- **The hash names the variant.** An icon board's hash is the set key
  (`board.html#phosphor`), which loads `../icons/phosphor.js`. A logo board's hash is the
  letter: each logo candidate is three files, `$WS/<section id>/logo-<letter>.svg`,
  `-mark.svg` (the symbol alone) and `-small.svg` (the 16px version), copies of each other
  where they don't differ, so the board always finds all three. The headers and the dark
  strip inline them (they follow `currentColor`); the tab and the 32px spot show the small
  file as an `<img>`, the way a browser draws a favicon. Ids inside the files (a `<mask>`)
  carry the letter, so files inlined into one page don't collide.
- **After the first logo pick**, `A` is what the record holds now (`assets/brand/`),
  labelled `기록 그대로`, not the old code.
- **Board height.** `check.cjs --frames` reports each board's page size under `boards`;
  set the iframe to it.

## Icons

`icons.cjs` gathers the sets so every board draws the same concepts:

    node "$WS/icons.cjs" find phosphor gear cog         # names in a set
    node "$WS/icons.cjs" collect "$WS/icons.json" "$WS/icons"

1. List the concepts the product uses (from the imports, plus what the screens need),
   each with an `id` and a Korean `label`.
2. Map each concept to a name in every candidate set with `find` (exact matches come
   first; try the set's own word too, `references/icons.md`, Names differ). Never guess a
   name; a concept a set doesn't have stays out of its map and shows as `없음`.
   When the record already names a set's version, pin it in the map
   (`"lucide": { "version": "1.81.0" }`), so the drawing is the settled one.
3. `collect` writes `$WS/icons/<set>.js` (downloads stay in `$WS/icons/vendor`). A board
   page writes `<i data-ic="settings" data-size="16"></i>` where an icon goes.
4. The captions carry, per set, what `collect` reported: version, license, how it draws,
   the nominal stroke at 16, 20 and 24px, and missing concepts. A set left out because it
   draws like another gets one line under the grid (`뺀 세트: Tabler, A와 그리는 방식이 같습니다`).

## Logos

Draw each candidate as SVG by hand, from the step's options in `references/logo.md`.

- **Text** uses a font file the board page loads with `@font-face`: the project's own
  fonts first, then open-licensed ones (`references/logo.md`, Typefaces). Record the
  license with the font.
- **Measure every candidate** at the sizes its spots use, from the file each spot shows
  (the `-small.svg` for 16 and 32):

      node "$WS/pixel.cjs" "$WS/r2-1/logo-B-small.svg" "$WS/r2-1/px" --name B \
        --sizes 16,32,180 --color '#1d4e89' --font "Pretendard=$WS/fonts/Pretendard-Bold.woff"

  It writes the PNGs in `--color`, the 8 times enlargement for 16 and 32, and per size
  `blur` (share of partly covered pixels) and `thin` (thinnest parts, in screen pixels).
  At 16px read `blur` first; `thin` is scaled from a large render. Compare these between
  candidates measured the same way; they are approximate. Text drawn from a font and the
  same text turned into outlines measure differently, so from the first logo pick on,
  measure outlined files only (`pixel.cjs outline` first), and say so once when a number
  differs from an earlier step's. `thin` sees holes inside the mark, not a gap open to
  the outside (between two shapes); give such a gap from the drawing in 16px pixels and
  check it in the enlargement. Give the current logo the font its page uses, or say on
  its caption that the measurement used another.
- **The header width** at 360px and the gap to the menu button are read with `check.cjs
  --frames --sel '<logo>, <menu button>' --props box` (each box is `x y width height`).

## Captions

Measured facts and judgments are kept apart.

- **Facts**, on the values line: `16px 흐린 픽셀 8% · 가장 가는 부분 1.6px · 360 헤더 폭 60px`,
  for icons `없는 개념 1 / 11 · 16px 획 1.33px · 라이선스 MIT`. Icon contrast is the `graphic`
  value of `check.cjs --a11y` (3:1), not `contrast`, which is for text. A failing one is still shown
  (`16px 가장 가는 부분 0.4px, 획이 끊깁니다`).
- **Judgments**, one line labelled `판단`: a shape the mark leans on that many marks
  share, or a resemblance to a brand from step 1 (`references/logo.md`); for an icon in
  I5, a reading the picture already carries elsewhere (sliders read as filters). `없음`
  when none.
- **Every logo candidate carries a `상표 검색 안 함` chip** (`dh-real` style). A search is
  the user's to do; it goes into `logo.md`'s `verify`.
- Gains and losses as usual (`shared/writing.md`, The caption).
- Every sentence rests on a measurement or on the drawing's own numbers, in screen
  pixels (never viewBox units). What only the eye says goes on the `판단` line.
- A candidate dropped because it resembled a brand from step 1 gets one line under the
  grid (`뺀 안: 접힌 모서리 메모지, 에버노트와 닮았습니다`).

The recommendation weighs the facts at the smallest spot first, then the judgments.

## Reading the response

| response | do |
|---|---|
| no identifiable candidate (`좋네`) | ask which one, or what to refine |
| a refinement (`B인데 조금 더 굵게`) | append a section, letters continue |
| a pick (`B로 갈게`) | record it (below) |
| `건너뛰기`, `나중에` | record the step as `보류` |
| another step named | that step is the next order |
| `○○처럼 만들어줘` (a real brand) | say in one line that this skill doesn't draw after a brand, and ask what about it appeals |

## Recording a pick

1. Screenshot the section as `$WS/pick-<section id>.png` (`check.cjs ... --section <id>`),
   so a later check on the same section doesn't overwrite it.
2. End with a `기록 지시:` block (`shared/decisions.md`) for `icons.md` or `logo.md`: the
   step's row, a D entry with the measured facts and the judgment line, the screenshot.
   The first pick in a track creates its file with step 1 in `## 바탕`.
3. **Icon set (I2):** the block writes the concept table (`개념`, `아이콘 이름`, `쓰는 곳`)
   from the map, with the set's version and license (`shared/decisions.md`, Brand files).
   Picking the current set changes no code; say so in one line.
4. **Logo files.** From L2 on, every logo pick also records the current files. Before
   copying, turn text into shapes so the files don't need the font:

       node "$WS/pixel.cjs" outline "$WS/r4-1/logo-C.svg" "$WS/fonts/Name-Bold.woff" "$WS/brand/logo.svg"

   Then export the small sizes: `pixel.cjs "$WS/brand/logo-small.svg" "$WS/brand" --sizes 16,32
   --color <primary> --png favicon-32:32` and, from the mark, `pixel.cjs "$WS/brand/logo-mark.svg"
   "$WS/brand" --color <foreground> --png apple-touch-icon:180:<background>:15` (15% padding).
   `favicon.svg` is the small version with its color written in (`fill="#1d4e89"` instead of
   `currentColor`): a tab draws the file as an image, where `currentColor` is black.
   The block copies the `$WS/brand/` files that changed with this pick to
   `design-decisions/assets/brand/` (of `logo.svg`, `logo-mark.svg`, `logo-small.svg`,
   `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`; all six on the first pick),
   replacing the previous ones; the replaced decision is archived
   as usual, its screenshot stays.
5. The report says, in Korean: what was settled, where it was written, and the next step.

## Ending

When the user says it is done (`끝났어`, `됐어`), list the steps still open in one line,
then tear down as `shared/liveview.md` says. Steps never reached stay out of the files;
only a step the user chose to skip is recorded as `보류`.
