# Security Policy

## Supported versions

Only the latest release (the newest `vX.Y.Z` tag) receives fixes. `manuwright update` installs it.

## Reporting a vulnerability

Please report security problems privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability** (private vulnerability reporting). Do not open a public issue for a vulnerability.

Include what you found, how to reproduce it, and the version (`manuwright --version`). You should receive an answer within 14 days.

## Scope

ManuWright runs locally on your computer and reads the paper folder you point it at. Reports of particular interest:

- a path that lets a project file read or write outside its paper folder;
- a way for a check to report PASS for input it did not verify;
- secrets (API keys) written into project files, logs, review packets or build outputs;
- manuscript, data or prompt-log content sent to a provider without the owner's explicit consent.

Clinical data never belongs in this repository or in an issue. Use synthetic examples in reports.
