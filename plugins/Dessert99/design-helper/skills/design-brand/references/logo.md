# Logo directions

Candidates come from the options below, drawn as SVG for this product's name and step 1.
Each section varies one step; everything later is held at its plainest.

## Forms (L2)

| form | what it is | gains | costs |
|---|---|---|---|
| 글자형 (wordmark) | the name in letters | the name is read everywhere | smears at 16px; weak as a trademark when the typeface is unchanged |
| 머리글자형 (lettermark) | one or two letters, often in a tile | survives at 16px | says little about the product; tiles with a letter are common |
| 심볼형 (symbol) | a shape alone | the clearest small mark | the name must be written beside it; a new shape takes time to be known |
| 조합형 (symbol with name) | a symbol and the name together, used apart when small | the name where there is room, the symbol where there isn't | two versions to keep |

Most web products end up with a combination: the full version in the header, the symbol
in the tab. Draw what the spots make of each form; don't argue it.

## Typefaces (L3)

- **The project's own fonts first**, with their license as the project has it.
- **Open-licensed fonts** (SIL OFL) otherwise. Get the files from the `@fontsource/<name>`
  npm package (`npm pack @fontsource/<name>` into `$WS/fonts`, then the `files/` folder
  holds woff and woff2) or the font's own release. Korean names: Pretendard, SUIT,
  Noto Sans KR, IBM Plex Sans KR, Gowun Dodum (all OFL). Latin names:
  Inter, Manrope, DM Sans, Space Grotesk, Fraunces (all OFL).
- Korean `@fontsource` packages split the glyphs over numbered subset files, so one file
  may lack the name's letters (`pixel.cjs outline` reports `missingGlyphs`). Prefer the
  font's full release (Pretendard: the `pretendard` npm package, about 70MB; extract only
  what you need: `tar xzf pretendard-*.tgz package/dist/web/static/woff/Pretendard-Bold.woff
  package/dist/LICENSE.txt`).
- Never a font whose license is unknown, and never a system font for the final mark: the
  file can't travel with the logo.
- A typeface step compares two to four faces that genuinely differ (geometric, humanist,
  rounded, a serif) at one weight: the heaviest weight every candidate has (often 700),
  said on the sheet when it differs from the current one. Weight and spacing are L5. At header size faces look
  alike: add one row with the header logo enlarged 4 times to that step's board.
- SUIT is not on `@fontsource`; it is the `@sun-typeface/suit` package.
- `pixel.cjs outline` needs TTF, OTF or WOFF. Keep one of those beside the woff2.

## Symbol directions (L4)

Each direction is named by the idea it uses, never by a look:

| direction | built from |
|---|---|
| 머리글자 변형 | the first letter's own shape, cut or joined |
| 기하 도형 | circles, squares, lines; meaning from arrangement |
| 하는 일의 은유 | an object or action the product is about (a page, a thread, a path) |
| 이름의 은유 | what the name itself means |

Two to four directions, each one plain drawing. A direction picked is refined in L5.

## Details (L5)

One attribute per section: the name's weight, letter spacing, the symbol's line weight
(when it is drawn with lines), corner radius, the symbol's size against the name, the gap
between them. Ladders of three to five in order, the current version in its place on the
ladder (labelled `현재값`), not moved to A.

## Small versions (L6)

The 16 and 32px version is a separate drawing, not the big one shrunk.

- Remove what `pixel.cjs` shows breaking: parts under 1px at 16 (`thin`), detail that
  turns into gray (`blur` above about 0.3).
- Snap straight edges to whole pixels of the 16px grid.
- Candidates: the full mark shrunk (as the baseline), the symbol alone, a simplified
  symbol, the first letter. When the small spot already shows the symbol alone, the first
  two are one drawing: use versions snapped to the grid at different sizes or gaps
  instead. Draw them in the tab and enlarged.

## Not like anyone else

- Never draw after a named brand. `토스 같은 느낌` becomes attributes (`굵고 둥근 글자`,
  `밝은 파랑`), and only those are drawn; the brand itself is never shown or traced.
- Brands from step 1 to avoid, and the best-known marks of the product's own field, are
  what candidates are checked against: a candidate that shares their form and shape is
  not shown.
- Shapes many marks share make a mark forgettable and hard to protect. Name it on the
  `판단` line when a candidate leans on one: a check mark, a lightning bolt, a leaf, a
  speech bubble, a globe, an infinity loop, a shield, a rocket, a letter in a rounded
  square, an abstract swirl.
- A wordmark in an unchanged typeface is weak as a trademark: say it once on its caption.
- Searching registered trademarks (KIPRIS in Korea) is the user's. Every logo candidate
  carries the `상표 검색 안 함` chip, and `logo.md` keeps it in `verify` until the user
  says it was done.
