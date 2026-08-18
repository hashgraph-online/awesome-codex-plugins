# Security Policy

## Supported version

Security and correctness fixes are applied to the current supported source line,
currently `0.6.x`.

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

Schema-5 turn dispositions are private, turn-bound control declarations. They
do not grant authority, prove that a dependency is real, or prove that evidence
is semantically relevant. A yielded turn keeps every unverified requirement
pending; only a valid private checkpoint can complete the guarded contract.
Under Stop protocol 1.1.0, legacy `continue` is advisory and cannot force
another turn. Only a hash-verified explicit-persistence instruction or an
uncheckpointed whole-task completion claim can activate a correction turn.

Historical cache repair trusts only the archive SHA-256 index. A missing,
unindexed, symlinked, or hash-mismatched archive fails closed; `--apply` never
uses a corrupt archive as repair input and archives are not automatically
deleted. `context-guard diagnose` exposes bounded hashes, protocol/control
sources, declared dispositions, reason codes, and observed diagnostic outcomes,
not raw prompts or replies.
