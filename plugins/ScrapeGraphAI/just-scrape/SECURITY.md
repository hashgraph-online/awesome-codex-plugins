# Security Policy

## Supported Versions

The latest published version of `just-scrape` on npm receives security updates.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately rather than
opening a public issue.

- Email: **security@scrapegraphai.com**
- Alternatively, use GitHub's [private vulnerability reporting](https://github.com/ScrapeGraphAI/just-scrape/security/advisories/new).

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce, or a proof of concept
- Any suggested remediation

We aim to acknowledge reports within 3 business days and to provide a remediation
timeline after triage. Please do not disclose the issue publicly until a fix has
been released.

## API Keys

`just-scrape` requires a ScrapeGraph AI API key, supplied via the `SGAI_API_KEY`
environment variable or a local `.env` file. Never commit API keys to source
control. Rotate any key that may have been exposed at
[scrapegraphai.com/dashboard](https://scrapegraphai.com/dashboard).
