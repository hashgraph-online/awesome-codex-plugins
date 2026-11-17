# Security policy

## Report a vulnerability

Report it privately, not in a public issue:

- On GitHub: open the [Security tab](https://github.com/moonetix/revenue-skills/security) of this repository and choose **Report a vulnerability**, or go straight to the [private report form](https://github.com/moonetix/revenue-skills/security/advisories/new).
- If you cannot use GitHub: email support@moonetix.com with "revenue-skills security" in the subject.

Say what is affected, how to reproduce it, and what an attacker gains. We will confirm that we received the report and tell you what we plan to do about it.

## Scope

In scope:

- The scripts that run on a user's machine: `probe.mjs` (for example a way past the loopback rule, the volume caps or the redirect rule, or a secret that reaches its output), `validate-findings.mjs` and `render-report.mjs` (for example reading files outside `--root`), and `economy-check.mjs`.
- Instructions in a skill that would lead an agent to do something unsafe, such as probing a host the user does not own or copying a live secret into a report.
- The repository tooling under `scripts/` and `.github/`.

Out of scope:

- `playground/vulnerable/` is vulnerable on purpose. Its bugs are the exercise. It binds to 127.0.0.1 and must never be deployed.
- `examples/` holds audits of old code, as they were written. The bugs they describe are the content.
- A money bug in `playground/fixed/` or a pattern in a builder skill that would lose money is welcome, but as an ordinary [issue](https://github.com/moonetix/revenue-skills/issues/new?template=missed-bug.yml): neither runs anywhere but on your machine.

## Supported versions

| Version | Fixes |
| --- | --- |
| 1.3.x | yes |
| 1.2.x and older | no, update to 1.3 |
