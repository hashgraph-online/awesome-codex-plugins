# Security Policy

## Supported versions

ru-text ships as a rolling latest version; security fixes land on the most recent release.
Please upgrade to the latest version before reporting.

| Version | Supported |
|---|---|
| Latest release | ✅ |
| Older releases | ❌ |

## What this plugin is

ru-text is a set of static Markdown files — text-quality rules, a plugin manifest, and slash
commands defined as Markdown. It collects no data, makes no network requests, and executes no
code (see [PRIVACY_POLICY.md](PRIVACY_POLICY.md)). The realistic security surface is therefore
small: the main risk is a malicious or mistaken rule edit reaching users through a pull request,
which is mitigated by review before merge.

## Reporting a vulnerability

Please report security issues privately — do not open a public issue.

- Preferred: GitHub [private vulnerability reporting](https://github.com/talkstream/ru-text/security/advisories/new) (Security → Report a vulnerability).
- Or email [nafigator@gmail.com](mailto:nafigator@gmail.com) with «ru-text security» in the subject.

Include the affected file or rule, a description of the issue, and steps to reproduce if applicable.

## What to expect

This is a best-effort, single-maintainer project. You can expect an acknowledgment within a few
days and a fix or response as soon as the issue is confirmed. Thank you for helping keep ru-text
and its users safe.
