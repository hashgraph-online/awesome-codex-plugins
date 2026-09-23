# Security Policy

## Supported versions

Security fixes are applied to the current public DevRecap release and to `main`.

## Reporting a vulnerability

Please report suspected security or privacy vulnerabilities privately through GitHub Security Advisories:

https://github.com/jquinteiroo/devrecap/security/advisories/new

Do not include credentials, private source code, raw coding-agent transcripts, personal data, or other unrelated sensitive information in the report.

A useful report includes:

- the DevRecap/plugin version;
- operating system and Node.js version;
- the affected command or workflow;
- minimal reproduction steps using synthetic or sanitized data;
- the security or privacy impact you observed.

Please do not open a public GitHub issue for an unpatched vulnerability. Public issues are appropriate for ordinary bugs, installation problems, and feature requests.

## Security model

DevRecap is explicit-invocation only. Local Codex history, Claude history, and Git evidence are accessed only after the user authorizes those sources. Git collection is guarded as read-only, and DevRecap does not run background filesystem watchers or repository mutation commands as part of recap generation.

If a generated report contains unexpected sensitive information, stop sharing the report and submit a private security report with sanitized reproduction details.
