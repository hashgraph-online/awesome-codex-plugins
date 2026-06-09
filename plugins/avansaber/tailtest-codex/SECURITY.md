# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 4.x     | Yes       |

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Email: support@avansaber.com

Include a description of the issue, steps to reproduce, and the potential impact.
You will receive a response within 5 business days. We ask that you give us reasonable
time to address the issue before public disclosure.

## Scope

tailtest hooks run locally on your machine. They do not make network requests, store
credentials, or transmit session data to external services. Session state is confined
to `.tailtest/session.json` in your project directory.
