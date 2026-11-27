# Sync by eye

design-sync's own instructions. Read `shared/core.md` first, then
`shared/decisions.md` (the record you read) and `shared/agent-guide.md` (the block the
apply leaves behind). Detection and blast radius follow `shared/stylesystems.md`. Paths
like `shared/sheet.md` are the plugin's shared folder (`shared/core.md`, Paths).

## What this skill does

It moves the record's `확정` rows into the code, one scope the user picked at a time.

- **Only `확정` rows move.** `초안`, `보류`, `보관` and `해당 없음` rows are skipped and
  listed once, in one line.
- **The record never changes here.** If the user wants a settled value to be different,
  that is a new decision: point to design-system in one line and leave the row alone.
- **The direction is record to code.** Tokens that exist only in the code are listed,
  never deleted.
- **Nothing is applied unseen.** The change is drawn before and after on the project's
  real screens, then applied to the scope the user picks.

## Steps

1. **Read the record.** Name the workspace `design-sync.XXXXXX`. Read `README.md` and
   every area file with `확정` rows. No record:
   say that there is nothing to sync yet, name design-system, and end the turn.
2. **Find the tokens in the code.** Detect the style system and read where each token is
   defined (file and line). Match record tokens to code tokens by name; where the record
   uses a role the code names differently, match by role. A match you can't establish
   from the code is a question for the user, one at a time.
3. **Diff.** Keep it in `$WS/memo.md`, one row per token: `추가` (in the record, not in
   the code), `변경` (different value), `같음`, `코드에만` (not in the record), and
   `건너뜀` (the record's row is not `확정`). A row moves only when its `상태` column is
   `확정` (`shared/decisions.md`); a settled role whose value is still a draft is
   `건너뜀`.

   Then look for **`우회`**: places where a settled role is used without its token. Each
   area file's table names where a role is used (`쓰는 곳`). Find those rules in the code
   and the property the role governs (color, font size, radius); a rule that sets it with
   a literal, or with a different token, bypasses the role. Equal values count too: a
   literal can't follow the token later. Each one is a row: `우회 app.css:11 .input
   font-size 14px (본문, 15px)`.
4. **Blast radius.** For every `추가` and `변경` row, count where the token is used, as
   `shared/stylesystems.md` says per fork. A count the search may have missed is a floor
   (`23곳 이상`).
5. **Draw it.** One section per area with changes, on the board (`shared/board.md`). A
   section's board is a frozen copy of the code as it is now, so `A 지금` keeps showing
   the before state after the apply. Draw `B 동기화 후` as the variant that applies the
   record's values:
   - CSS variables: the variant overrides the custom properties.
   - Tailwind v4: a second entry file in the section's folder that imports the project
     stylesheet and overrides the `@theme` values; B's page links that build.
   - Tailwind v3: a config in the section's folder that requires the project's config and
     overrides the changed keys; B's page links that build.
   - SCSS and CSS-in-JS: carry both value sets as CSS variables.
   - A `우회` row (step 3) is drawn too: B replaces the literal with the token, so the
     user sees what routing it through the role changes.

   A and B side by side need two boards' width. When they don't fit, put B under A.

   Captions list every changed token on the values line
   (`--radius-md 6px에서 8px로 · 23곳`), and line 3 says what changes on screen. The cost
   slot names the edit (`tokens.css 1줄`). Run `check.cjs --frames --a11y` on both; a pair
   below the record's `verify` is said on the caption of the side it is on. Below the
   section, recommend which scope to apply first and why.
6. **Scope.** The user picks in chat: everything, an area, single tokens, and whether the
   `우회` rows go with them. A reply that doesn't name a scope gets one question. When
   only one change exists, the question is yes or no.
7. **Hand off.** The final message says, in Korean, what will change and its blast
   radius, then ends with `반영 지시:`:

        반영 지시:
        - 범위: 색 영역 (토큰 4개)
        - 고칠 곳: src/styles/tokens.css:12 `--color-accent: #2563eb;` → `--color-accent: #0074e2;`
        - 고칠 곳: ...
        - 안내 블록: 넣기 (처음)            (or `갱신`, when it already exists)
        - 검증: 위 토큰의 정의가 바뀌었는지, 프로젝트 빌드와 린트

   Token definitions change, plus the `우회` rows the user included (the literal becomes
   `var(--token)`). A token renamed by the record also lists every usage to rename. The
   `안내 블록:` line appears on every apply and says which files exist
   (`넣기 (처음, AGENTS.md 새로 만듦, CLAUDE.md 있음)`); the main agent asks before the
   first insertion (`shared/agent-guide.md`). With no build or lint in the project, the
   `검증` line says so and checks the definitions and that the old value is gone.
8. **After `반영 완료:`.** Diff again from the changed code, `우회` rows included, and
   report what is left in one or two lines. Nothing left: say so, and that the draft rows
   are decided in design-system.

## Ending

When the user says it is done (`끝났어`, `됐어`), tear down as `shared/liveview.md` says.
