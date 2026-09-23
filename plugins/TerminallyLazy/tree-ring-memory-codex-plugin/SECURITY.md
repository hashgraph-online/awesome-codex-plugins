# Security Policy

## Supported Versions

The `main` branch is the supported version of this agent plugin package.

The Tree Ring Memory framework and CLI are maintained in the canonical
repository:

<https://github.com/TerminallyLazy/Tree-Ring-Memory>

## Reporting A Vulnerability

Report vulnerabilities privately through the canonical repository's GitHub
security advisory form:

<https://github.com/TerminallyLazy/Tree-Ring-Memory/security/advisories/new>

Use the canonical issue tracker only for non-sensitive support:

<https://github.com/TerminallyLazy/Tree-Ring-Memory/issues>

Never include vulnerability details, secrets, tokens, private memory contents,
or personal data in a public issue.

## Data Handling

This wrapper plugin contains guidance files and bounded local lifecycle-hook
registrations. It does not run a background service, include remote MCP
servers, collect telemetry, or store credentials. The hooks run only at
`SessionStart`, `SubagentStart`, `Stop`, and `SubagentStop`, forward standard
input directly to the local Tree Ring CLI, and do not persist prompts,
transcripts, `last_assistant_message`, or hook input. They are synchronous,
bounded to 10 seconds, and never run as a `SessionEnd` or background recorder.

Stop hooks enforce one agent-mediated checkpoint. They may supply an exact
strict `tree-ring capture` template only for concise durable candidates. Strict
capture fixes agent scope, requires harness identity and provenance, accepts
only normal sensitivity, and tags the result as automatic capture. A missing,
sensitive, ambiguous, or ungrounded candidate must not be stored.

Tree Ring Memory is designed for explicit agent-mediated memory actions. Store
only concise decisions, lessons, warnings, and evidence references that are
useful, source-linked, and privacy-safe. Do not store raw transcripts, secrets,
private keys, tokens, or raw chain-of-thought.
