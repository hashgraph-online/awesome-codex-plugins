# Security policy

Thanks for reporting security issues responsibly. This page explains how to reach the
maintainer privately and what to expect.

## Which versions get fixes

falsegreen-skill is in its first development cycle. Security fixes land on the latest
commit on `main`. There is no long-term support branch yet.

| Version | Supported |
|---------|-----------|
| `main`  | yes |
| tagged releases below the latest | no |

## Attack surface

This package is mostly prompt and documentation assets (`SKILL.md`, `reference.md`,
`schema/`) plus a thin CLI (`bin/falsegreen-llm.js`). The CLI has zero runtime
dependencies and does not import or execute the code it scans.

The one thing to understand before using the CLI: **it sends your test files to a
third-party LLM provider.** `falsegreen-skill analyze <file>` reads the test source and
posts it to the provider you select (Anthropic, OpenAI, Gemini, or an OpenAI-compatible
endpoint) over HTTPS, using the protocol in `llm.md` as the system prompt. So:

- The test code leaves your machine. Do not run it on files that must not reach an external
  service. The provider's data-retention policy applies, not ours.
- The provider API key is read from an environment variable. Keep it out of shell history,
  CI logs, and committed config.
- `--base-url` lets you point the openai-compatible provider at an arbitrary host. Point it
  only at endpoints you trust; the test code goes wherever you send it.

Realistic vulnerability reports concern the CLI: a path that leaks the key, an injection in
how files or arguments are handled, or the request going somewhere other than the selected
provider.

## How to report a vulnerability

Do **not** open a public GitHub issue for security problems. Use a private channel:

- **GitHub Security Advisories (preferred):** <https://github.com/vinicq/falsegreen-skill/security/advisories/new>
- **Email:** `vinicq@gmail.com` with the subject prefix `[falsegreen-skill security]`.

Include a short description and impact, steps to reproduce, the version tested, and whether
it has been disclosed elsewhere.

## What to expect

- An acknowledgement within five business days.
- A reproduction or follow-up within ten business days.
- A fix or a clear "won't fix" rationale before any public disclosure.
- Credit in the release notes if you want it.

## What is not a security issue

File these as regular issues: a wrong or missed judgment (the analysis is probabilistic), a
provider returning malformed output, or a finding you disagree with. The fact that the CLI
transmits code to a provider is by design and documented above, not a vulnerability.
