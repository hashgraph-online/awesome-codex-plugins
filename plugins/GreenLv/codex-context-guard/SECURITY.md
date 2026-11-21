# Security Policy

## Supported version

Security and correctness fixes target the latest published version, currently `0.17.1`. Check the [GitHub Release](https://github.com/GreenLv/codex-context-guard/releases/latest) for the published package. The [versioning policy](docs/VERSIONING.md) explains how source and package changes are verified.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** flow in the repository Security
tab. Do not open a public issue for suspected credential exposure, path escape,
state-integrity bypass, Hook command injection, or completion-gate bypass.

Include the affected version, operating system, Codex version, reproduction
steps, and the smallest sanitized evidence needed to demonstrate the issue. Do
not attach raw prompts, transcripts, plugin-private state, credentials, or user
data.

## Security boundary

Context Guard is a local correctness sidecar, not a security sandbox. It cannot
make an untrusted Hook safe, prove semantic correctness, or replace operating
system access controls. Users must review and trust the exact Hook definition
before enabling it.

Private session state uses schema 13 with turn-bound private control records.
They do not grant authority, prove that a dependency is real, or prove that
evidence is semantically relevant. A yielded turn keeps every unverified
requirement pending; only a valid private checkpoint can complete the guarded
contract. Under Stop protocol 5.0.0, legacy `continue` remains advisory and
cannot force another turn; only a hash-verified explicit-persistence
instruction or an uncheckpointed whole-task completion claim can activate a
correction turn.

Consumed versioned caches are immutable. This product provides no archive
repair or automatic deletion of old caches; installation uses official Codex
marketplace operations. A cache's continued presence does not prove which
runtime an existing task loads. `context-guard diagnose` exposes bounded
hashes, protocol/control sources, declared dispositions, reason codes and
observed diagnostic outcomes, not raw prompts or replies.

Redaction in derived evidence, diagnostics, and exports covers the documented
supported domain (see [privacy](docs/PRIVACY.md)): common structured
credential fields, authorization headers, URL userinfo and query values, and
several common token shapes. It is defense in depth, not recognition of
arbitrary unknown secrets; review every export before sharing it.
