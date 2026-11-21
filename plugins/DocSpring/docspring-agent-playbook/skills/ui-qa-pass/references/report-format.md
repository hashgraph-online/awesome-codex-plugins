# The QA report

Read this before you write the report. The report is for a reader who hasn't watched the pass: they should be able
to make every decision from it without opening the app.

## Structure

Keep this order. The user's time goes to the decisions, so they come first.

1. **Header.** Branch, commit SHA, date, where it ran (local stack), and one line on what changed for people.
2. **Decisions for the user.** One numbered item per real trade-off: the question, the options, your recommendation
   and why, and the screenshot that shows it. Write each so it can be answered in a word ("D2: yes").
3. **Defaults you'll take unless they object.** A short list of small calls you made (a label's wording, a spacing
   value), one line each.
4. **Findings by area.** One section per area letter. For each finding: its ID, the screen and state, width and
   theme, what was wrong, what you changed (file and a few words), and the before and after shots side by side.
   Label every shot with the state it shows.
5. **What wasn't tested, and why.** Screens, states, browsers or widths you skipped, and anything you couldn't force
   (a third-party failure, an email you couldn't receive locally).

```markdown
# QA: <branch> at <short SHA>, <date>

<One line on what changed for people.>

## Decisions
D1. <Question>. Options: A) ..., B) .... I recommend B because .... [screenshot]

## Defaults I'll take unless you object
- <Small call>, because ....

## A. <Area>
### A1. <Screen>, <state> (<width>, <theme>): <what was wrong>
Fixed in `<file>`: <what changed>.
| Before | After |
| --- | --- |
| ![A1 before: ...](a1-before.webp) | ![A1 after: ...](a1-after-R2.webp) |

## Not tested
- <What>, because ....
```

## Later rounds

Each round of the user's feedback becomes a new "Round N" section at the top, with that round's decisions, fixes and
shots, above the earlier rounds. Publish to the same place each time so the link stays the same.

## Images

- Use cropped copies of the screenshots, focused on what each finding is about, converted to WebP or compressed PNG
  to keep the page small. Keep the full-size originals in `QA_DIR/screenshots/`.
- Copy only the images and the report page out of `QA_DIR`. Never the folder itself: its browser profile holds cookies
  and its login files hold passwords.
- Crop out anything that shouldn't travel: other accounts' names or email addresses, tokens shown on screen, and
  anything that looks like real customer data (which a QA pass shouldn't use in the first place).
- Write alt text that says what each image shows ("Settings at 390px, dark: error text overflowing the card").

## Destinations

Use the destination the settings name (`QA reports are published to:` under `### Local stack and QA`). If none is set,
ask the user once, offering these, and offer to add the answer to the settings:

- **A private hosted page**, such as a Claude artifact or your platform's equivalent. Build the page from the cropped
  images and republish to the same address so the link stays the same. Publish the page and every image together each
  round, then check that every image loads. Keep the page's source and images in `QA_DIR/report/` so it can be
  rebuilt.
- **A PR comment with images.** Put the report's text in the comment and attach the images to the comment (most code
  hosts accept image uploads in the comment editor). Don't commit screenshots to the branch.
- **A static page** on a host your team already uses for internal pages: an `index.html` with the images beside it.
  Check who can read the host before you publish there.

Wherever the report goes, once the branch has a PR, draft the short QA comment as well (date, commit SHA, what passed,
what wasn't tested), and post it when the settings allow posting comments or after the user approves the text. No
secrets, credentials or customer data in either.
