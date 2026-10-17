# Runtime Profile Policy

Use this when runtime evidence needs setup details without leaking private access or binding to one engineering form.

## Runtime Profile

A runtime profile is a neutral description of how to exercise a flow:

- entry action or command;
- required setup state;
- safe test identity or anonymized fixture;
- external dependency availability;
- artifact directory;
- redaction rules.

## Redaction Rules

- Store handles, run IDs, and request IDs.
- Redact contact details, tokens, keys, private payloads, account names, and hostnames.
- Record unavailable dependencies as blockers instead of inventing successful evidence.

## Validation

- Confirm the profile lets another agent repeat the run without private knowledge.
- Confirm the artifact manifest records profile name, command, started time, result, and classification.
- Confirm sensitive values are absent from committed summaries.

## Do Not Include

- Real account names, keys, hosts, or contact details.
- Claims that a runtime path was tested without artifact evidence.
- Setup steps that only work on one private machine.
