---
name: verify-playground
description: Launch, check, drive, prove, and bug bash the e2e playground web app (apps/testbed) with e2e. Use before claiming a playground change works, when asked to verify or screenshot a page, or to bug bash it.
---

# Verify the playground

Read the e2e skill first (`npx e2e guide` prints it). This skill only says what is true
of this app. The config is `e2e.config.ts` (target `web`, tests
`tests/**/*.e2e.ts`); the bug bash uses `e2e.bugbash.config.ts`.

## Launch

The target's `app.command` runs `node app/server.mjs` with `PORT=4271`. The
runner starts it, waits for `http://127.0.0.1:4271`, and stops it after the
run. Nothing to start by hand. The app needs no env, seeds, or database;
todos live in the browser's localStorage, the session in a cookie. To
watch the app by hand, `pnpm app` serves it on the same port, and a run
then stops with `APP_ALREADY_RUNNING` until it is stopped. The port is
fixed, not reused.

## Doctor

```bash
npx e2e list tests/smoke.e2e.ts       # loads the config, starts nothing; exit 0 and four pairs
npx e2e run tests/smoke.e2e.ts        # starts the app, opens it, pins the Playground heading; exit 0
```

`list` failing is the config or a dependency. `run` failing with
`APP_ALREADY_RUNNING` is a server of yours on the port, and
`LOCATOR_NOT_FOUND` on the heading is the app itself. A signed-in check
is a test that consumes a named session, `npx e2e run
tests/dashboard.e2e.ts`: selecting it runs the `admin` setup behind it
and checks the restored signed-in state. Running `tests/auth.setup.e2e.ts` on
its own selects no test and exits `NO_TESTS`. Run Doctor first whenever
anything looks off.

## Drive

Live, over the registered `e2e mcp` server: `open_session`, then
`observe`, the verbs, and `locate` before writing any locator (topic
`mcp`). The catalog offers `type_secret` for the `admin` credential and no
project tools. Scripted: a test under `tests/`, `screen` for every control
in the feature map (all have accessible names), `agent.act` for a flow
that varies. Signed-in tests start from the `admin` session that
`tests/auth.setup.e2e.ts` saves (`{ session: 'admin' }`); `admin-cookie`
is the same account signed in without a fill, so screenshots stay.

## Evidence

Every run writes `.e2e/report.json`. `--trace on` writes
`.e2e/results/<test>/trace.md` for passing tests too; `--video` records
each attempt under the test's `attempt-<n>/`; `app.screenshot('<name>')`
saves a named frame. The next run clears `.e2e/results/`, Doctor
included, so a proof that must outlive it runs with `--output
.e2e/proof/<name>`. A proof drives the page the way a user does, the nav
link or the route, the labelled control, the button, and captures the
action and the state after it, not only the final screen. Side effects:
todos are `localStorage.todos` (read with `browser.evaluate`), the session
is the `session` cookie (`browser.cookies()`); the server keeps nothing.

## Bug bash

`e2e.bugbash.config.ts` (untracked) spreads `e2e.config.ts`, adds
`tests/bugbash/**` to the glob, a model, and the `skeptic` and `fuzzer`
personas; its `context` says what is not a bug here (seeded data, the
admin account, no email). The charters are in [features/](features/), one
H2 per feature, already in the `slug|target|agent|charter` line format the
fan-out in topic `bug-bash` step 3 reads. `.e2e/bugbash/` is in
`.gitignore`, with `.e2e/proof/`. One explorer at a time needs no isolation change; several
need `pnpm app` started first and `reuseExisting: true` on the command,
since the port is fixed. A finding is a bug once
`tests/bugbash/<slug>.e2e.ts` fails on the reported defect, as topic
`bug-bash` step 6 reads it; anything else is the explorer's claim.

## Cleanup

The runner stops the app it started; `close_session` stops the one a
session started; a `pnpm app` you started is yours to stop (its pid, never
`pkill node`). Remove `.e2e/bugbash/<slug>/` for a charter whose findings
were all rejected; a charter the report cites stays until the user has the
report. Keep `.e2e/results/`, `.e2e/proof/`, `.e2e/report.json`, and the
videos under each attempt. That is the proof, and all of it is gitignored.

## Helpers

None. The e2e CLI is the helper.
