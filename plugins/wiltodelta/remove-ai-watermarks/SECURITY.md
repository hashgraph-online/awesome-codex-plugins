# Security policy

## Supported versions

Security fixes go into the latest release. Older releases are not patched;
upgrade through the channel you installed from (PyPI or Homebrew).

## Reporting a vulnerability

Report vulnerabilities privately through
[GitHub private vulnerability reporting](https://github.com/wiltodelta/remove-ai-watermarks/security/advisories/new).
Do not open a public issue for an unpatched vulnerability. Include the affected
version, the command or API call, and a minimal input that reproduces it.

Vulnerabilities in a dependency, such as a CVE in a package from `uv.lock`, can
be reported as a regular issue when the advisory is already public.

## Dependency vulnerabilities

Dependabot raises alerts and update pull requests for `uv.lock` and GitHub
Actions, and CI scans `uv.lock` with
[`uv-secure`](https://github.com/owenlamont/uv-secure) on every push and pull
request. A vulnerable dependency is upgraded to a fixed release; advisories
without one are tracked under
[Known security-gate blocks](docs/development.md#known-security-gate-blocks).
