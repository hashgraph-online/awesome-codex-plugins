# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately through GitHub's Security
Advisories ("Report a vulnerability" on this repository) so they can be fixed
before disclosure.

Do not open a public issue for a vulnerability that could put users at risk.

## Scope

- Code in this repository: hooks, scripts, skills, tests, and prompts.
- The plugin installation and hook-trust flow (trust is hash-keyed; an update
  invalidates the old trust and requires re-trusting).

## Response

We aim to acknowledge reports within 3 business days and to ship a fix as soon
as practical. Because hook trust is hash-keyed, users must re-trust hooks and
start a new thread after any update that changes the hook definitions.
