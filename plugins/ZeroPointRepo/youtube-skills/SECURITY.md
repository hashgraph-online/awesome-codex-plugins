# Security Policy

## Reporting a Vulnerability

If you find a security issue in these skills or in the TranscriptAPI service they call, please report it privately.

- Email: hello@transcriptapi.com with the subject line "SECURITY: youtube-skills"
- Please include: the affected file or endpoint, steps to reproduce, and the impact you believe it has.
- Do not open a public GitHub issue for security reports.

We acknowledge reports within 3 business days and aim to ship a fix or mitigation within 14 days for confirmed issues. We will credit reporters in the release notes unless you ask us not to.

## Scope

- The skill definitions in this repository (SKILL.md files and reference documents).
- The interaction patterns they instruct agents to use against the TranscriptAPI service (api.transcriptapi.com).

Out of scope: vulnerabilities in YouTube or Google properties (report those to Google), and issues in third-party agent runtimes that load these skills.

## Handling of Credentials

These skills never embed credentials. API keys are supplied by the user through environment configuration at runtime and are never written into skill files. If you find any credential committed to this repository, treat it as a vulnerability and report it via the channel above.

TranscriptAPI is a third-party, independent service. It is not affiliated with, endorsed by, or sponsored by YouTube or Google.
