# Security

Report a vulnerability through [GitHub private vulnerability reporting](https://github.com/andreaborio/abliterate/security/advisories/new). Include:

- the affected release, and the command, skill or Action input;
- the expected and observed behavior.

Use synthetic data: do not attach credentials or customer repositories. Ordinary false positives or false negatives with a safe example can go in public issues.

## What abliterate does and does not do

- **The engine is read-only on the repository.**
  - It runs `git` with external diff drivers, textconv, fsmonitor and hooks disabled.
  - It never executes code from the repository, installs dependencies, fetches or changes branches.
  - It skips files over 1 MB.
- **Network** is used only by:
  - `deps`: package names and versions to `api.osv.dev`, CVE ids to `api.first.org`, and a download of the CISA KEV feed;
  - `variants --from`: a public advisory or GitHub patch.

  No source code, file path or repository identity is sent. `--offline` disables the network and uses the local cache.
- **Secrets** matched by the engine are redacted in its output. The skill instructs agents never to repeat secret values.
- **The pre-push hook** is installed only by `abliterate hook install`, never as a side effect, and does not block unless `ABLITERATE_BLOCK=1`.
- **The GitHub Action:**
  - builds the engine from the action's own source with `npm ci --ignore-scripts`;
  - pins third-party actions by commit;
  - runs agents read-only;
  - skips the agent step on pull requests from forks.
- **There is no abliterate model, service or telemetry.** The agent you choose (Claude Code, Codex) performs the review under its own data and execution policies.
- **The skill** is defensive. It treats diffs, comments and tool output as untrusted data, never runs the code under review, and limits test inputs to benign values.
