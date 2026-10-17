# Security policy

## Supported versions

Only the latest release on PyPI gets security fixes.

## Reporting a vulnerability

Please report it privately through the repository's
[Security tab](https://github.com/MohammadHijjawi97/since-cutoff/security) ("Report a
vulnerability"). If that option is not available, open an issue that asks for a private
contact, without any details of the problem.

Useful to include: the since-cutoff version, the command or MCP tool call, and the package or
project that triggers the problem.

## Scope

since-cutoff reads untrusted input: package archives from PyPI, model answers, and the project
it scans. It is designed never to import or execute package code or model-written code: package
sources are read statically (only `.py`/`.pyi` files are extracted, with path and size checks),
and model answers are only type-checked. A way to make it execute such code, write files other
than its cache, its reports (`.since-cutoff/` or the paths you give) and the marked
`AGENTS.md`/`CLAUDE.md` block, or send your source code to a model provider is a
vulnerability.
