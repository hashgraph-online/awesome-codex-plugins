# Security policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository. Do not open a public issue containing credentials, private memory data, a working exploit, or a path to another user's local files.

Include the affected version, operating system, Codex version, reproduction steps, and the smallest redacted diagnostic sample that demonstrates the problem. Never attach a TMCRA token file, provider key, memory database, prompt transcript, or integration state directory.

## Intended security boundary

- The plugin accepts only exact loopback TMCRA API destinations.
- Bearer tokens remain in owner-only files and are read at request time.
- Recalled memory is labelled as untrusted data before injection.
- User and assistant records remain role-separated and source-attributed.
- Hook failures are fail-open for Codex and write only bounded, content-free diagnostics.
- The plugin never contacts a TMCRA account service or hosted TMCRA endpoint.

The TMCRA runtime, model providers, operating-system backups, and any separately installed integrations have their own security boundaries.
