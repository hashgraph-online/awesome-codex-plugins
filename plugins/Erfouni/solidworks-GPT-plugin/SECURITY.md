# Security policy

## Supported versions

Security fixes are applied to the latest release and the current `main`
branch. Older snapshots are not maintained separately.

## Reporting a vulnerability

Please use
[GitHub private vulnerability reporting](https://github.com/Erfouni/solidworks-GPT-plugin/security/advisories/new)
for vulnerabilities involving plugin instructions, local scripts, knowledge-base
requests, consent handling, or feedback submission. Do not open a public issue
until a fix or coordinated disclosure is ready.

Include the affected version, a minimal reproduction, expected impact, and any
suggested mitigation. Remove API keys, proprietary CAD documents, customer
data, and other secrets from the report. The maintainer will acknowledge the
report, assess severity, and coordinate remediation through the private
advisory.

## Security boundaries

- The plugin does not bundle SolidWorks or grant access to a SolidWorks
  installation; it uses automation surfaces already available to Codex.
- Knowledge-base reads may use the configured `SW_KB_HOST`. Treat a custom host
  as trusted infrastructure before connecting to it.
- Session feedback stays local unless the user explicitly sends it or has
  previously saved the `always` preference.
- Secrets must come from environment variables. They must not be committed,
  placed in prompts, or included in feedback payloads.
- Generated CAD macros and exported models must be reviewed and validated
  before production use.

This policy covers the public plugin repository. Vulnerabilities in SolidWorks,
Codex, GitHub Actions, or the configured knowledge-base service should also be
reported to the relevant vendor or operator.
