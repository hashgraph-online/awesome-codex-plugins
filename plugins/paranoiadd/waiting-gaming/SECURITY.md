# Security

The current release is supported on Windows with local Codex execution.

Report vulnerabilities privately to the maintainer through
[GitHub private vulnerability reporting](https://github.com/paranoiadd/waiting-gaming/security/advisories/new).
Include the affected version, reproduction steps, expected behavior, and impact.
Please keep credentials and conversation contents out of reports.

The plugin runs native Windows programs through trusted Codex lifecycle hooks.
It stores hashed turn identifiers, event times, native window and process
identifiers, game scores, the board, and window position in its plugin data directory.
Gameplay runs locally and has no network dependency. Source code is under
`src/`, and `build.ps1 -Test` builds and checks the distributed programs.
