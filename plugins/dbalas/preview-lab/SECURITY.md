# Security policy

## Reporting a vulnerability

Report it privately through [GitHub's vulnerability reporting](https://github.com/dbalas/preview-lab/security/advisories/new), not in a public issue. You will get an answer within a week. Only the latest release gets fixes.

## What Preview Lab does on your machine

- Runs Node scripts with no dependencies: `skills/preview-lab/scripts/pl.mjs` and `capture.mjs`.
- Starts Chrome, Edge or Chromium headless to screenshot the URLs the agent passes in.
- Serves the review page on `127.0.0.1` only. It answers only requests whose `Host` and `Origin` are that address, serves only files inside the lab folder, and stops after the feedback is sent.
- Keeps its files in `~/.preview-lab/` (or `PREVIEW_LAB_HOME`), outside your project, and deletes labs whose checkout is gone.
- Makes no network requests of its own and collects no telemetry.
