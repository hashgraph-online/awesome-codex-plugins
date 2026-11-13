# Planning the state matrix

Read this before the first screenshot of a pass. It turns the diff into the list of shots to take. Choose from these
lists by what the change could break: exercise the changed interaction fully, sample the rest, and record the matrix
you tested and its gaps in the report.

## 1. List what people see change

- Start from `git diff --stat <base>...` and read every view, component, stylesheet, marketing or docs page, email
  template, error message and translation file the branch touches.
- Follow shared code outward. A changed shared component, layout or stylesheet changes every page that uses it: find
  its users (`git grep`) and shoot a sample, including the most used page and the one with the most unusual layout.
- Note screens the change removes or moves, and check that their old links still go somewhere sensible.

## 2. States for each screen

| State | Examples | What tends to go wrong |
| --- | --- | --- |
| Empty | No records yet, a new account, a search with no results | Missing empty message, a table header with nothing under it, a call to action that leads nowhere |
| Loading or in progress | A spinner, a queued job, a file uploading | Layout jumps when content arrives, a spinner that never stops, buttons left clickable |
| Done | Success message, the new record in the list | Stale counts, a success message that stays forever |
| Failed | Server error, validation error, network failure, timeout | Raw error text, a form that loses what the person typed, no way to retry |
| Disabled | No permission, a read-only record, a plan or feature limit | A control that looks enabled, a control whose value doesn't match the effective setting |
| Limits | Maximum length, maximum items, quota reached, rate limit hit | Text cut off without a hint, a limit message that names the wrong number |
| Long text | Long names, long words with no break points (URLs, email addresses, commands, IDs), translated copy if you ship other languages | Overflow out of cards and table cells, buttons pushed off screen |
| Many items | Hundreds of rows, a long dropdown, deep nesting | Missing pagination or scroll, slow rendering, sticky headers that cover content |
| Who is looking | Signed out, the owner, another member, a different role if the app has roles | A visitor seeing an owner's data, or an owner missing a control |

## 3. Paths through each flow

For each flow the branch touches, walk these paths as well as the happy one:

- Skip an optional step.
- Cancel halfway, then start again.
- Retry after a failure (force the failure first, see the skill's "Force each state").
- Go back with the browser's back button.
- Reload halfway through, including right after a submit.
- Submit twice quickly.

## 4. Themes

Shoot changed app screens in each theme the product supports when the change touches layout, color, images or
icons; a copy-only change needs one theme. Check contrast, borders and dividers that vanish against the background,
images and icons with transparent or white backgrounds, hard-coded colors, and focus rings. A theme switch in the
browser emulates the operating system's setting; if the app also stores the person's own choice, set that too.

## 5. Widths

| Width (CSS px) | Why |
| --- | --- |
| 1440 x 900 | Desktop, the default |
| 1024 | Screens with side-by-side panes (a preview beside an editor, a sidebar beside a form), with each pane's panels open. Panes that look right at 1440 get squeezed, headings wrap, and an empty column can take another pane's width. |
| 768 | Tablet |
| 390 | Phone |
| 320 | Anywhere a long word can overflow (a command or URL in a copy field) |
| 667 x 375 | A phone held sideways, for anything drawn once it scrolls into view: it can be taller than two screens |

Pick the widths where the change could look different: the default desktop width always, the narrower ones when the
layout is responsive or has panes, and 320 wherever a long word appears. A copy change needs the width where its text
is longest.

Narrowing the window doesn't emulate a phone. To check touch behavior (hover-only menus, touch handlers, the mobile
viewport), use your tool's device emulation: in Playwright, a browser context created with
`isMobile: true, hasTouch: true` (the example runner only changes the width). Some
tools reload the page when touch emulation turns on or off (Puppeteer does), so an open dialog or a state reached by a
form submit is lost. Change the width first, then reach the state, and close dialogs before you change back.

## 6. Hidden content

- A multi-step form often keeps its other steps on the page but hidden. Go to each step before its screenshot, and
  don't measure an element on a hidden step: its size reads as 0.
- Tabs, accordions and menus: open each one that the branch changes.
- If a page shows the wrong theme, check whether the app stores its own theme choice (a cookie or local storage) as
  well as following the system setting, and set both.

## 7. What to check in every shot

- Every control's value, and separately whether the viewer can change it: which checkbox is ticked, which option is
  selected, what an input holds, which way a toggle points. Each control shows the effective value; disabling a
  control doesn't change its value.
- Text: truncation, overflow, wrapping, wrong or leftover placeholder copy, inconsistent names for the same thing.
- Alignment and spacing: measure them with `qa.boxes()` or `getBoundingClientRect()` on every page that shares the
  layout, rather than judging by eye.
- Contrast in each supported theme.
- Keyboard focus is visible, and the tab order makes sense on changed forms.
- The browser console: each error is a finding.

## 8. The findings list

Keep it in `QA_DIR/findings.md` as you go, one row per finding. Give each area a letter (A: settings page, B: upload
flow) and number its findings (A1, A2, B1), so the user can answer "B2: go with your recommendation".

```markdown
| ID | Screen and state | Width, theme | What's wrong | Before | After | Status |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | Settings, save failed | 390, dark | Error text overflows the card | a1-before.png | a1-after-R2.png | Fixed |
| A2 | Settings, empty | 1440, light | Empty message says "No items"; "No API keys yet" is clearer | a2-before.png | | Decision |
```
