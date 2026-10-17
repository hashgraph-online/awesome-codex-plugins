# Security Policy

## Supported versions

Security fixes are applied to the latest published release line. Earlier
release lines may receive fixes at the maintainers' discretion, but are not
considered supported unless explicitly stated otherwise.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting or a private Security
Advisory for this repository. Do not include live credentials, private project
files, prompts, command output, or other users' data in a public issue.

Include the affected version, the relevant entrypoint or Atom contract, a
minimal synthetic reproduction, expected behavior, and observed behavior. Do
not test credentials, access unrelated files, or exercise remote side effects.

## Security model

The plugin intentionally reads user-authorized local project metadata and can
execute user-authorized local commands. These capabilities are bounded by:

- strict argv, input, task-count, output, and timeout limits;
- typed dependency, artifact, effect, capacity, and lifecycle contracts;
- fail-closed unknown-effect handling;
- immutable plan-envelope and semantic hashes;
- source-snapshot validation before execution;
- POSIX process-group or Windows Job Object cancellation, with broker boundaries
  called out explicitly, and no automatic retry of uncertain side effects;
- explicit opt-in for bounded local trace routing signals.

The bundled indicator includes MCP Ext Apps, the MCP SDK, Zod, and a small
tree-shaken Zod-to-JSON-Schema contribution. Its build forces Zod's eval/JIT
capability probe to `false`, verifies the emitted dependency/license closure,
and rejects `eval`/`new Function` regressions. The indicator does not load remote
scripts or contact remote destinations.

A successful scan or test suite reduces known risk but is not proof of complete
security.
