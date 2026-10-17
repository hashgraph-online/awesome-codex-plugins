# Security Policy

## Supported scope

This repository currently covers:

> `Aegis Method Pack (runtime-ready)`

Security reports should focus on issues that are actually in scope for this repository, such as:

- plugin installation or distribution issues
- host integration behavior in the published method-pack surface
- documentation or packaging issues that could mislead users into unsafe usage

This repository is **not** the authority for a future `Runtime Core`, and should not be reported as if it already provides that layer.

## How to report a security issue

Please do **not** open a public GitHub issue for security-sensitive reports.

Instead, contact the maintainer privately through one of these paths:

1. GitHub security advisory / private vulnerability reporting, if enabled on the public release repository
2. If that path is not yet enabled, contact the repository maintainer directly and include:
   - affected version or commit
   - affected host or installation path
   - reproduction steps
   - impact description
   - whether the issue is public anywhere else

## Security contacts

| GitHub | Role |
| --- | --- |
| [@GanyuanRan](https://github.com/GanyuanRan) | Repository owner and maintainer |
| [@ryanchou1994](https://github.com/ryanchou1994) | Security contact; helps triage and validate reports, with focus on `hooks/`, `scripts/`, and `tests/` |

## What to include

Useful reports usually include:

- exact version or commit
- host environment
- installation method
- steps to reproduce
- observed impact
- any logs, transcripts, or screenshots that help confirm the issue

## Response expectations

The goal is to:

1. acknowledge the report
2. validate whether it is actually in scope for `Aegis Method Pack`
3. determine whether the issue belongs here, in a host platform, or in a different layer
4. coordinate a fix and disclosure path

## Out of scope examples

The following are commonly out of scope for this repository:

- issues that reproduce without Aegis installed
- host platform vulnerabilities unrelated to this method pack
- future runtime-core authority claims that do not exist in this repository

If a report actually belongs to a host platform, the maintainer may redirect it to the correct upstream project.
