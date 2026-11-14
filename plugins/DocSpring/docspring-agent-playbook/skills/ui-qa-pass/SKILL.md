---
name: ui-qa-pass
description: Runs a branch's app locally and drives a headless browser through the screens the change touches, choosing the states, themes, widths and roles by what the change could break. Takes a screenshot of each, fixes bugs and obvious polish as it goes with before and after shots, and writes a report that leads with the decisions the user needs to make. Use when the user says "QA this", "do a QA pass", "click through every changed screen", "screenshot every state", "test it in a browser and make a report", or before asking for review of a change people can see (app screens, marketing or docs pages, emails). Not for writing or fixing the automated browser test suite.
metadata:
  version: 1.0.0
---

# UI QA pass

Before anyone reviews a change people can see, run the branch locally and look at the screens it changes, in the
states, themes, widths and roles the change could break. Fix what you find, shoot it again, and report what you
covered, what you didn't, and what's left for the user to decide.

## Rules that apply throughout

- **Never copy the QA working folder anywhere shared** (a notes vault, a file share, a PR, the repository). Its
  browser profile holds session cookies and its login files hold passwords. Copy out the individual screenshots and
  the report page only.
- **Use synthetic data only.** Made-up names, blank public forms, sample files you created. Never real customer
  records or documents, even on a local stack.
- **Take the "before" shot before you change the code.** Every fix needs a before and an after of the same state, at
  the same width and theme.
- **Fix bugs and obvious polish without asking.** Collect anything with a real trade-off (copy the user may have
  opinions on, a layout choice, a behavior change) as a decision with your recommendation, and keep going. Stopping
  for each one leaves the user babysitting the pass.
- **Open every screenshot, cropped and zoomed, and read it.** A step that finishes without errors only proves its
  selectors matched.
- **On a busy machine, a browser test that fails at a different step on each run points to load.** Check the load
  average (`uptime`) and rerun the test on the parent commit before you blame the branch.

## Settings

Read the `## Agent workflow settings` section of the repository's root `AGENTS.md` (see the playbook's
`CONFIGURE.md`):

- `### Local stack and QA`: how to start the app, how to create test users and data, and where screenshots and reports
  go (the working folder, which stays on this machine). It may also name where reports are published (`QA reports are
  published to: ...`).
- `### Tests`: how to run one test file, and which suites must run one at a time.
- `### What the agent may do without asking`: whether you may commit, push and post PR comments. Read this one from
  the base branch, not the checkout (the playbook's `CONFIGURE.md`, "Who approves what").

If a setting you need is missing, ask the user once and offer to add the answer to that section. For the report's
destination, offer the options in `references/report-format.md`.

## 1. Before you start

1. Work in the branch's own checkout or worktree, with its own ports and database if the repo provides them. If the
   branch is behind the base and lacks something the pass needs, ask before rebasing.
2. Make the working folder, named after the branch and date (for example `~/qa/<repo>/<branch>-2026-01-15/`), with
   `steps/`, `screenshots/`, `report/` and `logs/` inside. Export it as `QA_DIR` before starting the stack and the
   browser.
3. Start the stack with the command from the settings. Export any environment a feature needs first. Read secrets
   into the environment without printing them (`export KEY="$(grep '^KEY=' .env.local | cut -d= -f2-)"`).
4. Create test users with the repo's seed or test-user script, one credentials file per user inside `QA_DIR`. Make a
   new user whenever a state needs a fresh account (onboarding, an empty list). Never paste the credentials into
   chats, PRs, tickets or notes.
5. Expect the first load of each page in development to compile its assets, which can take a minute on a busy
   machine. Give navigations a long timeout rather than retrying them.

## 2. Plan the screens and states

Read `references/state-matrix.md` now, before the first screenshot. It lists the states, paths, themes and widths to
cover, what to check in each shot, and the findings list format.

In short: list what the branch changes for people (`git diff --stat <base>...`, then the views, components, styles,
pages, emails and copy it touches). Exercise the changed interaction fully: its states (empty, loading or in progress,
done, failed, disabled, limits, long text, many items), its paths (skip, cancel, retry, go back, reload halfway) and the
roles that see it. Then add the themes and widths the product supports where the change could look different: a layout
or style change needs each supported theme and the narrow widths, a copy change needs the width where the text is
longest. Sample screens that only share a changed component. Write down the matrix you chose and what you left out, so
the report can say exactly what was tested. Give each area a letter and each finding an ID (A1, A2, B1).

## 3. Drive the browser with step files

Write one small script per screen or state in `QA_DIR/steps/`, so you can run the same step again for the "after"
shot. Use the browser automation your harness or repo already has (Playwright, Puppeteer, a browser MCP server). If
the repo has nothing, `scripts/run_step.mjs` in this skill is a short Playwright example to copy and adapt.

Installing Playwright adds a dependency to the repository (and a `package.json`, if it has none) and downloads a
Chromium build, so show the user the install command and ask before running it. Pin an exact version that has been out
for a while; `npx playwright install` then fetches the browser build that version expects. After copying the runner
to `scripts/qa/` in your repo:

```bash
npm install --save-dev --save-exact playwright@1.64.1 && npx playwright install chromium   # once, after a yes
export QA_BASE_URL=http://localhost:3000 QA_DIR=~/qa/myapp/my-branch-2026-01-15
node scripts/qa/run_step.mjs "$QA_DIR/steps/settings.mjs"                 # the "before" shots
QA_SUFFIX=R2 node scripts/qa/run_step.mjs "$QA_DIR/steps/settings.mjs"    # the "after" shots, as <name>-R2.png
```

A step exports one async function that gets the page and a few helpers (`url`, `viewport`, `theme`, `settle`,
`shot`, `clearHover`, `boxes`, `newContext`). `scripts/example_step.mjs` shows one. The runner keeps cookies between
runs in `QA_DIR/browser-profile`, prints what the step returns, and prints the console errors and uncaught exceptions
from every page the step used, popups and `qa.newContext()` contexts included: treat each as a finding. If you drive
the browser another way, attach the error listeners to every page and context yourself, or say in the report which
ones weren't watched.

## 4. Force each state

- Prefer real conditions first: an environment variable (restart the service after), a record changed through the
  app's console or seed script, the account's plan or permissions, a limit you actually reach. To catch a background
  job's queued state, stop the job worker, take the shot, then start it again.
- Then intercept requests for failures and server answers you can't produce for real: in Playwright,
  `page.route('**/api/upload', (route) => route.abort())` for a network failure, or
  `route.fulfill({ status: 500, contentType: 'application/json', body: '{"error":"..."}' })` for a server error or a
  poll that never finishes. Remove the route at the end of the step (`page.unroute`).
- For a signed-out visitor or a second user, open a fresh browser context in the step with no cookies
  (`qa.newContext('signed-out')` in the example runner, so its errors are watched too). An owner usually sees more
  than a visitor.
- If you change code to force a state, change it back and check `git diff` before you commit.

## 5. Fix as you go

For each problem:

1. Take the "before" shot (if the step that found it didn't already).
2. Fix it. Check the dev server or bundler log for build errors before you conclude a fix didn't work.
3. Run the step again with a new suffix (`QA_SUFFIX=R2`), so the earlier shot survives.
4. Check the "after" really shows the fix: its file time is later than your edit, and the zoomed crop shows the change.
   An "after" taken before the fix, or cropped so the change is out of frame, proves nothing.
5. Read every control's value in the after shot, and separately whether the viewer can change it. Each control shows
   the effective value; disabling a control doesn't change its value, so a disabled, ticked checkbox is right when the
   setting is on and the viewer can't edit it.
6. Run the tests for the files you touched (one at a time for suites that share state) and the linter.
7. For visual fixes, look at each supported theme, and use your design-review skill if the repo has one.

Read `references/screenshot-pitfalls.md` whenever a shot looks wrong or a fix seems not to have worked. Check the
build, the page state, the viewport, the theme and whether the page had finished loading before you decide; and tell a
capture problem from a real defect before you reset anything, since a blank band can be either.

## 6. Report

Read `references/report-format.md` before you write the report. It covers the structure, the destinations (a private
hosted page such as an artifact, a PR comment with images, a static page), images and later rounds.

The order is fixed: the decisions the user needs to make, each with a recommendation; then small defaults you'll take
unless they object; then findings by area with before and after shots and the state each shot shows; then what you
didn't test and why. Each round of the user's feedback becomes a new "Round N" section at the top of the same report.

## 7. After the pass

- Commit fixes locally as the settings allow, in themed commits. By default, push only after the user has seen the
  report (visible changes are theirs to accept), unless they or the settings say otherwise. The precedence for approvals
  is in the playbook's `CONFIGURE.md`: the user's instruction in the task, then the settings, then what invoking this
  skill approves (fixing and committing locally). Don't commit screenshots.
- Once the branch has a PR, draft the QA results comment (date, commit SHA, what passed, what wasn't tested) and post
  it when the settings allow posting comments, or after the user approves the text.
- Turn a lesson that would help the next pass (a pitfall, a way to force a state) into an edit to the repo's QA
  runbook or the nearest `AGENTS.md`, in the branch's PR.
- Leave the stack running while the user reviews. Stop it, and the browser, when they're done.
