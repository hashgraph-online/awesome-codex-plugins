# Security policy

## Reporting a vulnerability

Report security problems privately through GitHub: open the [Security tab](https://github.com/requie/endostack/security) of this repository and choose **Report a vulnerability**. Don't open a public issue for a security problem.

Include the affected file or skill, the agent you were using, steps to reproduce, and what an attacker gains. You will get a first reply within five business days. Fixes ship in a patch release with credit to the reporter unless you ask not to be named.

## In scope

- Code in this repository: the installer, the build and lint scripts, and the bundled tools (`statechart`, `watch-pr`, `orch`, `check-plan`, `worktree-audit`, the decision log and the issue-loop helpers).
- Skill or playbook text that leads an agent to take an unsafe action, such as following instructions found in untrusted content, skipping an approval step, or exposing secrets.
- The issue-loop GitHub Actions workflows and their token permissions.

## Out of scope

- Vulnerabilities in the coding agents themselves or in their model providers. Report those to the vendor.
- The demo app in `skills/try-endostack/demo/`. It ships with a deliberate path traversal trap for the `/try-endostack` demo. Its check script writes a `.env` holding one marker line into the demo folder; no credential ships with it.

## Supported versions

Security fixes go into the latest release only.
